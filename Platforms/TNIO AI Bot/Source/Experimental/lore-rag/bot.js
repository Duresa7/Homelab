const { Client, GatewayIntentBits, Partials } = require('discord.js');
const fs = require('fs');

function loadEnv(path) {
  if (!fs.existsSync(path)) return;
  for (const line of fs.readFileSync(path, 'utf8').split(/\r?\n/)) {
    if (!line || line.trim().startsWith('#')) continue;
    const idx = line.indexOf('=');
    if (idx === -1) continue;
    const key = line.slice(0, idx).trim();
    const value = line.slice(idx + 1).trim();
    if (key && !(key in process.env)) process.env[key] = value;
  }
}

loadEnv('/home/REDACTED_DEPLOYMENT_USER/lore-rag/discord-bot/.env');

const REQUEST_LOG_PATH = process.env.BOT_REQUEST_LOG || '/home/REDACTED_DEPLOYMENT_USER/lore-rag/logs/agent-requests.log';
const FEEDBACK_LOG_PATH = process.env.BOT_FEEDBACK_LOG || '/home/REDACTED_DEPLOYMENT_USER/lore-rag/logs/agent-feedback.log';

function logEvent(payload) {
  try {
    const line = JSON.stringify({ ts: new Date().toISOString(), ...payload }) + '\n';
    fs.appendFile(REQUEST_LOG_PATH, line, () => {});
  } catch {
    /* never let logging break a reply */
  }
}

function logFeedback(payload) {
  try {
    const line = JSON.stringify({ ts: new Date().toISOString(), ...payload }) + '\n';
    fs.appendFile(FEEDBACK_LOG_PATH, line, () => {});
  } catch {
    /* never let feedback logging break the bot */
  }
}

// In-memory map of bot replies → original question/sources, used to correlate
// emoji reactions back to the answer they're rating. Entries TTL'd after 48h.
const botRepliesById = new Map();
const REPLY_RECORD_TTL_MS = 48 * 60 * 60 * 1000;

function rememberBotReply(messageId, payload) {
  botRepliesById.set(messageId, { ...payload, t: Date.now() });
  // Lazy GC: prune entries older than the TTL whenever the map grows.
  if (botRepliesById.size > 500) {
    const cutoff = Date.now() - REPLY_RECORD_TTL_MS;
    for (const [id, record] of botRepliesById) {
      if (record.t < cutoff) botRepliesById.delete(id);
    }
  }
}

const token = process.env.DISCORD_TOKEN;
const channelId = process.env.DISCORD_CHANNEL_ID;
const loreAnswerUrl = process.env.LORE_ANSWER_URL || 'http://127.0.0.1:19731/agent-answer';
const displayName = process.env.BOT_DISPLAY_NAME || 'AI Librarian';

if (!token || !channelId) {
  console.error('Missing DISCORD_TOKEN or DISCORD_CHANNEL_ID');
  process.exit(1);
}

const COOLDOWN_MS = 10000;
const MAX_QUESTION_CHARS = 1200;
const SESSION_CONTEXT_MS = 2 * 60 * 60 * 1000; // 2 hours
const MAX_CONTEXT_MESSAGES = 10;
const REQUEST_MAX_SECONDS = 50;
const REQUEST_HTTP_TIMEOUT_MS = 60000;

const COOLDOWN_REPLY = 'One moment. The archives need a few seconds between requests.';
const TOO_LONG_REPLY = 'That request is too broad for a single archive pull. Ask it in a shorter form.';
const EMPTY_REPLY = 'State the question after the mention, and I will respond.';
const ERROR_REPLY = 'The archive lectern is not responding cleanly right now. Try again shortly.';

const cooldowns = new Map();
const channelSessions = new Map();

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
    GatewayIntentBits.GuildMessageReactions,
  ],
  partials: [Partials.Channel, Partials.Message, Partials.Reaction, Partials.User],
});

function stripMention(content, userId) {
  return content
    .replace(new RegExp(`<@!?${userId}>`, 'g'), '')
    .replace(/\s+/g, ' ')
    .trim();
}

function cleanContextText(text, userId) {
  return stripMention(String(text || ''), userId)
    .replace(/https?:\/\/\S+/g, '[link]')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, 500);
}

function pruneSession(channelKey, now = Date.now()) {
  const rows = channelSessions.get(channelKey) || [];
  const kept = rows
    .filter((row) => now - row.ts <= SESSION_CONTEXT_MS)
    .slice(-MAX_CONTEXT_MESSAGES);
  channelSessions.set(channelKey, kept);
  return kept;
}

function rememberSessionMessage(channelKey, role, content, userId, now = Date.now()) {
  const clean = cleanContextText(content, userId);
  if (!clean) return;
  const rows = pruneSession(channelKey, now);
  rows.push({ role, content: clean, ts: now });
  channelSessions.set(channelKey, rows.slice(-MAX_CONTEXT_MESSAGES));
}

async function fetchReplyContext(message) {
  const refId = message.reference?.messageId;
  if (!refId) return null;
  try {
    const replied = await message.channel.messages.fetch(refId);
    const role = replied.author?.id === client.user?.id
      ? 'Librarian'
      : (replied.author?.displayName || replied.author?.username || 'User');
    const content = cleanContextText(replied.content, client.user.id);
    if (!content) return null;
    return { role, content, ts: replied.createdTimestamp || Date.now() };
  } catch {
    return null;
  }
}

function sanitizeAnswer(text) {
  if (!text) return '';
  return String(text)
    .replace(/openclaw/gi, 'the lore system')
    .replace(/chatgpt/gi, 'the archive')
    .replace(/openai/gi, 'REDACTED_PRIVATE_ORG_LABEL United')
    .replace(/ollama/gi, 'the lore system')
    .replace(/\bgpt[-\s]?\d[\w.-]*/gi, 'the lore system')
    .replace(/qwen\S*/gi, 'the lore system')
    .trim();
}

function stripInlineCitations(text) {
  return String(text || '')
    .replace(/\s*\[\s*\d+(?:\s*[,;]\s*\d+)*\s*\]/g, '')
    .replace(/\s+([.,;:!?])/g, '$1')
    .replace(/ {2,}/g, ' ')
    .trim();
}

function escapeMarkdownLinkText(text) {
  return String(text || 'Source')
    .replace(/\[/g, '［')
    .replace(/\]/g, '］')
    .replace(/\n/g, ' ')
    .trim();
}

function formatSources(result) {
  const sources = Array.isArray(result?.sources) ? result.sources : [];
  if (!sources.length) return '';
  const lines = [];
  const seen = new Set();
  for (const source of sources) {
    const url = source.source_url || source.url || source.webViewLink;
    if (!url) continue;
    const sectionBits = [];
    const section = source.section || source.sheet_title;
    if (section) sectionBits.push(section);
    if (source.row_number) sectionBits.push(`row ${source.row_number}`);
    const detail = sectionBits.length ? ` - ${escapeMarkdownLinkText(sectionBits.join(', '))}` : '';
    const key = `${url}|${detail}`;
    if (seen.has(key)) continue;
    seen.add(key);
    const id = Number.isInteger(source.source_id) ? source.source_id : lines.length + 1;
    const title = escapeMarkdownLinkText(source.title || source.source_title || `Source ${id}`);
    lines.push(`[${id}] [${title}](${url})${detail}`);
    if (lines.length >= 5) break;
  }
  return lines.length ? `\n\nSources:\n${lines.join('\n')}` : '';
}

function chunkMessage(text, max = 1900) {
  const chunks = [];
  let remaining = text;
  while (remaining.length > max) {
    let split = remaining.lastIndexOf('\n', max);
    if (split < 500) split = remaining.lastIndexOf(' ', max);
    if (split < 500) split = max;
    chunks.push(remaining.slice(0, split).trim());
    remaining = remaining.slice(split).trim();
  }
  if (remaining) chunks.push(remaining);
  return chunks;
}

async function askLore(question, sessionContext) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_HTTP_TIMEOUT_MS);
  try {
    const res = await fetch(loreAnswerUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: question,
        session_context: sessionContext,
        limit: 5,
        max_seconds: REQUEST_MAX_SECONDS,
      }),
      signal: controller.signal,
    });
    if (!res.ok) throw new Error(`lore answer HTTP ${res.status}`);
    return await res.json();
  } finally {
    clearTimeout(timer);
  }
}

client.once('clientReady', () => {
  console.log(`${displayName} logged in as ${client.user.tag}; watching channel ${channelId}`);
});

client.on('messageCreate', async (message) => {
  try {
    if (message.author.bot) return;
    if (message.channelId !== channelId) return;
    if (!message.mentions.has(client.user)) return;

    const now = Date.now();
    const last = cooldowns.get(message.author.id) || 0;
    if (now - last < COOLDOWN_MS) {
      await message.reply({ content: COOLDOWN_REPLY, allowedMentions: { repliedUser: false } });
      return;
    }
    cooldowns.set(message.author.id, now);

    const question = stripMention(message.content, client.user.id);
    if (!question) {
      await message.reply({ content: EMPTY_REPLY, allowedMentions: { repliedUser: false } });
      return;
    }
    if (question.length > MAX_QUESTION_CHARS) {
      await message.reply({ content: TOO_LONG_REPLY, allowedMentions: { repliedUser: false } });
      return;
    }

    const replyContext = await fetchReplyContext(message);
    const recentContext = pruneSession(message.channelId, now);
    const sessionContext = replyContext ? [...recentContext, replyContext] : recentContext;

    await message.channel.sendTyping();
    const askStart = Date.now();
    const result = await askLore(question, sessionContext);
    const elapsedMs = Date.now() - askStart;

    const baseAnswer = stripInlineCitations(sanitizeAnswer(result?.answer || ''));
    const withSources = result?.mode === 'archive' ? baseAnswer + formatSources(result) : baseAnswer;
    const finalAnswer = withSources.trim() || ERROR_REPLY;

    logEvent({
      kind: 'agent_answer',
      user: message.author.username || message.author.id,
      channel: message.channelId,
      question,
      mode: result?.mode || 'unknown',
      route: result?.evidence?.route,
      confidence: result?.confidence,
      sources: (result?.sources || []).map((s) => s.title || s.source_title).slice(0, 5),
      candidate_count: result?.evidence?.candidate_count,
      elapsed_ms: elapsedMs,
      answer_preview: finalAnswer.slice(0, 240),
      context_messages: sessionContext.length,
    });

    rememberSessionMessage(message.channelId, 'User', question, client.user.id);
    rememberSessionMessage(
      message.channelId,
      'Librarian',
      finalAnswer.replace(/\n\nSources:[\s\S]*$/i, ''),
      client.user.id,
    );

    const sentMessageIds = [];
    for (const part of chunkMessage(finalAnswer)) {
      const sent = await message.reply({ content: part, allowedMentions: { repliedUser: false } });
      if (sent?.id) sentMessageIds.push(sent.id);
    }

    // Remember the *first* bot reply so reactions on it correlate back to the
    // question. Reactions on follow-up parts are still captured because every
    // chunk message ID is registered.
    for (const id of sentMessageIds) {
      rememberBotReply(id, {
        user: message.author.username || message.author.id,
        userId: message.author.id,
        channel: message.channelId,
        question,
        mode: result?.mode,
        confidence: result?.confidence,
        sources: (result?.sources || []).map((s) => s.title || s.source_title).slice(0, 5),
      });
    }
  } catch (err) {
    console.error('message handling failed:', err);
    logEvent({
      kind: 'agent_error',
      user: message.author?.username || message.author?.id,
      channel: message.channelId,
      question: stripMention(message.content || '', client.user?.id || ''),
      error: String(err?.message || err),
    });
    await message.reply({
      content: ERROR_REPLY,
      allowedMentions: { repliedUser: false },
    }).catch(() => {});
  }
});

// --- Reactions feedback -------------------------------------------------- //
//
// Users can react to the bot's answer with thumbs/X/etc. We log each reaction
// alongside the original question + sources so we can later analyze which
// answers/sources tend to score well or poorly. No live behavior change: this
// is signal we collect, not gate on.
async function handleReaction(reaction, user, action) {
  try {
    if (user?.bot) return;
    // Partials may need to be fetched.
    if (reaction.partial) {
      try { await reaction.fetch(); } catch { return; }
    }
    if (reaction.message?.partial) {
      try { await reaction.message.fetch(); } catch { return; }
    }
    const messageId = reaction.message?.id;
    if (!messageId) return;
    const record = botRepliesById.get(messageId);
    if (!record) return; // not a tracked bot reply

    const emoji = reaction.emoji?.name || reaction.emoji?.id || '?';
    logFeedback({
      kind: 'reaction',
      action,
      emoji,
      reaction_user: user?.username || user?.id,
      reaction_user_id: user?.id,
      bot_message_id: messageId,
      original_user: record.user,
      original_user_id: record.userId,
      channel: record.channel,
      question: record.question,
      mode: record.mode,
      confidence: record.confidence,
      sources: record.sources,
    });
  } catch (err) {
    // Never let feedback handling crash anything.
    console.error('reaction handling failed:', err);
  }
}

client.on('messageReactionAdd', (reaction, user) => handleReaction(reaction, user, 'add'));
client.on('messageReactionRemove', (reaction, user) => handleReaction(reaction, user, 'remove'));

client.login(token);
