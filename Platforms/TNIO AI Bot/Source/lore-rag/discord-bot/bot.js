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
const NEGATIVE_FEEDBACK_LOG_PATH = process.env.BOT_NEGATIVE_FEEDBACK_LOG || '/home/REDACTED_DEPLOYMENT_USER/lore-rag/logs/agent-negative-feedback.jsonl';
const ABSTAIN_FEEDBACK_LOG_PATH = process.env.BOT_ABSTAIN_FEEDBACK_LOG || '/home/REDACTED_DEPLOYMENT_USER/lore-rag/logs/agent-abstain-feedback.jsonl';
const REPLY_RECORD_LOG_PATH = process.env.BOT_REPLY_RECORD_LOG || '/home/REDACTED_DEPLOYMENT_USER/lore-rag/logs/agent-reply-records.jsonl';

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

function logNegativeFeedback(payload) {
  try {
    const line = JSON.stringify({ ts: new Date().toISOString(), ...payload }) + '\n';
    fs.appendFile(NEGATIVE_FEEDBACK_LOG_PATH, line, () => {});
  } catch {
    /* never let feedback logging break the bot */
  }
}

function logAbstainFeedback(payload) {
  try {
    const line = JSON.stringify({ ts: new Date().toISOString(), ...payload }) + '\n';
    fs.appendFile(ABSTAIN_FEEDBACK_LOG_PATH, line, () => {});
  } catch {
    /* never let feedback logging break the bot */
  }
}

function logReplyRecord(payload) {
  try {
    const line = JSON.stringify({ ts: new Date().toISOString(), ...payload }) + '\n';
    fs.appendFile(REPLY_RECORD_LOG_PATH, line, () => {});
  } catch {
    /* never let reply indexing break the bot */
  }
}

// In-memory map of bot replies → original question/sources, used to correlate
// emoji reactions back to the answer they're rating. Entries TTL'd after 48h.
const botRepliesById = new Map();
const REPLY_RECORD_TTL_MS = 48 * 60 * 60 * 1000;

function rememberBotReply(messageId, payload) {
  const record = { ...payload, bot_message_id: messageId, t: Date.now() };
  botRepliesById.set(messageId, record);
  logReplyRecord({ kind: 'bot_reply_record', ...record });
  // Lazy GC: prune entries older than the TTL whenever the map grows.
  if (botRepliesById.size > 500) {
    const cutoff = Date.now() - REPLY_RECORD_TTL_MS;
    for (const [id, record] of botRepliesById) {
      if (record.t < cutoff) botRepliesById.delete(id);
    }
  }
}


function loadBotReplyRecord(messageId) {
  try {
    if (!fs.existsSync(REPLY_RECORD_LOG_PATH)) return null;
    const lines = fs.readFileSync(REPLY_RECORD_LOG_PATH, 'utf8')
      .trim()
      .split(/\r?\n/)
      .slice(-5000)
      .reverse();
    for (const line of lines) {
      if (!line || !line.includes(messageId)) continue;
      try {
        const parsed = JSON.parse(line);
        if (parsed.bot_message_id === messageId) {
          const { ts, kind, ...record } = parsed;
          record.t = Date.now();
          botRepliesById.set(messageId, record);
          return record;
        }
      } catch {
        // Keep scanning older records.
      }
    }
  } catch {
    /* best effort only */
  }
  return null;
}

const token = process.env.DISCORD_TOKEN;
const channelId = process.env.DISCORD_CHANNEL_ID;
const loreAnswerUrl = process.env.LORE_ANSWER_URL || 'http://127.0.0.1:19731/agent-answer';
const displayName = process.env.BOT_DISPLAY_NAME || 'AI Librarian';
const ackReaction = process.env.BOT_ACK_REACTION ?? '👀';
const searchReaction = process.env.BOT_SEARCH_REACTION ?? '🔎';
const writeReaction = process.env.BOT_WRITE_REACTION ?? '✍️';
const doneReaction = process.env.BOT_DONE_REACTION ?? '✅';
const errorReaction = process.env.BOT_ERROR_REACTION ?? '❌';

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
const TYPING_REFRESH_MS = 8000;
const SEARCH_REACTION_AFTER_MS = 5000;
const WRITE_REACTION_AFTER_MS = 20000;

const COOLDOWN_REPLY = 'One moment. The archives need a few seconds between requests.';
const TOO_LONG_REPLY = 'That request is too broad for a single archive pull. Ask it in a shorter form.';
const EMPTY_REPLY = 'State the question after the mention, and I will respond.';
const ERROR_REPLY = 'The archive lectern is not responding cleanly right now. Try again shortly.';
const ACCURACY_FOOTER = '*Please check the Google Drive archive to verify accuracy. AI can make mistakes sometimes.*';

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
  return String(content || '')
    .replace(new RegExp(`<@!?${userId}>`, 'g'), '')
    .replace(/<@&\d+>/g, '')
    .replace(/<@!?\d+>/g, '')
    .replace(/<#\d+>/g, '')
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
    .replace(/\bSource:\s*[^.\n]*?\s+Sheet:\s*[^.\n]*?\s+Row:\s*\d+\s+Primary:\s*/gi, '')
    .replace(/\b(?:Source|Sheet|Row|Primary|Column\s+[A-Z])\s*:\s*/gi, '')
    .replace(/\s*[-–]?\s*Column\s+[A-Z]\s*:\s*/gi, ': ')
    .replace(/openclaw/gi, 'the lore system')
    .replace(/chatgpt/gi, 'the archive')
    .replace(/openai/gi, 'REDACTED_PRIVATE_ORG_LABEL United')
    .replace(/ollama/gi, 'the lore system')
    .replace(/\bgpt[-\s]?\d[\w.-]*/gi, 'the lore system')
    .replace(/qwen\S*/gi, 'the lore system')
    .replace(/\s+([.,;:!?])/g, '$1')
    .replace(/ {2,}/g, ' ')
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


function normalizeWhitespace(text, maxChars = 4000) {
  return String(text || '')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, maxChars);
}

function compactSources(sources) {
  return (Array.isArray(sources) ? sources : []).slice(0, 8).map((source, index) => ({
    source_id: Number.isInteger(source.source_id) ? source.source_id : index + 1,
    title: source.title || source.source_title || null,
    section: source.section || source.sheet_title || null,
    row_number: source.row_number || null,
    url: source.source_url || source.url || source.webViewLink || null,
    match_type: source.match_type || null,
    score: source.score ?? null,
    excerpt_preview: normalizeWhitespace(source.excerpt || source.text || source.content || '', 700),
  }));
}

function compactEvidence(evidence) {
  if (!evidence || typeof evidence !== 'object') return null;
  return {
    route: evidence.route || null,
    candidate_count: evidence.candidate_count ?? null,
    queries: Array.isArray(evidence.queries) ? evidence.queries.slice(0, 10) : undefined,
    hints: Array.isArray(evidence.hints) ? evidence.hints.slice(0, 20) : undefined,
    auto_sweep_terms: Array.isArray(evidence.auto_sweep_terms) ? evidence.auto_sweep_terms.slice(0, 30) : undefined,
    tool_calls: Array.isArray(evidence.tool_calls) ? evidence.tool_calls.slice(0, 20) : undefined,
    tool_log: Array.isArray(evidence.tool_log) ? evidence.tool_log.slice(0, 20) : undefined,
    sift: evidence.sift || undefined,
  };
}

function classifyQuestionKind(question, mode) {
  const q = String(question || '').toLowerCase();
  if (mode === 'persona') return 'persona_or_banter';
  if (/\b(rebel scum|scum|insult|joke|banter|who are you|how are you|feeling|yourself|say something|roast)\b/.test(q)) {
    return 'persona_or_banter';
  }
  if (/\b(tnio|sith|jedi|imperial|empire|inquisition|praetorian|mandalorian|codex|rank|ship|starship|droid|beast|force|saber|lightsaber|guild|character|lore|academy|cipher|hunter|sergeant|apprentice|master engineer)\b/.test(q)) {
    return 'archive_lore';
  }
  return 'unknown_or_general';
}

function isNegativeFeedbackEmoji(emoji) {
  const raw = String(emoji || '').trim();
  const lower = raw.toLowerCase().replace(/[\s_-]+/g, '');
  return raw === '❌'
    || raw === '✖'
    || raw === '✖️'
    || lower === 'x'
    || lower === 'crossmark'
    || lower === 'cross'
    || lower === 'novote'
    || lower === 'no'
    || lower === 'negative_squared_cross_mark'.replace(/[\s_-]+/g, '');
}

function isAbstainFeedbackEmoji(emoji) {
  const raw = String(emoji || '').trim();
  const lower = raw.toLowerCase().replace(/[\s_-]+/g, '');
  return raw === '🤷'
    || raw === '🤷‍♂️'
    || raw === '🤷‍♀️'
    || raw === '⚪'
    || raw === '◻️'
    || raw === '⬜'
    || raw === '➖'
    || raw === '〰️'
    || lower === 'abstain'
    || lower === 'abstainvote'
    || lower === 'neutral'
    || lower === 'mixed'
    || lower === 'partial'
    || lower === 'partiallyright'
    || lower === 'sortof'
    || lower === 'meh'
    || lower === 'shrug'
    || lower === 'whitecircle'
    || lower === 'white_large_square'.replace(/[\s_-]+/g, '')
    || lower === 'heavy_minus_sign'.replace(/[\s_-]+/g, '');
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
    if (lines.length >= 8) break;
  }
  return lines.length ? `\n\nSources:\n${lines.join('\n')}` : '';
}

function appendAccuracyFooter(text) {
  const body = String(text || '').trim();
  if (!body) return ACCURACY_FOOTER;
  if (body.includes(ACCURACY_FOOTER)) return body;
  return `${body}\n\n${ACCURACY_FOOTER}`;
}

function stripAccuracyFooter(text) {
  return String(text || '').replace(ACCURACY_FOOTER, '').trim();
}

async function removeOwnReaction(message, emoji) {
  if (!emoji) return;
  try {
    const reaction = message.reactions.cache.find((r) => r.emoji?.name === emoji || r.emoji?.id === emoji);
    if (reaction) await reaction.users.remove(client.user.id);
  } catch {
    /* best effort only */
  }
}

function startStatusReactionSequence(message) {
  const statusEmojis = [ackReaction, searchReaction, writeReaction, doneReaction, errorReaction]
    .filter(Boolean);
  let current = null;
  let stopped = false;
  const timers = [];

  const setStatus = async (emoji) => {
    if (stopped || !emoji || emoji === current) return;
    const previous = current;
    current = emoji;
    if (previous) await removeOwnReaction(message, previous);
    try {
      await message.react(emoji);
    } catch (err) {
      console.warn('status reaction failed:', err?.message || err);
    }
  };

  setStatus(ackReaction).catch(() => {});
  if (searchReaction) timers.push(setTimeout(() => setStatus(searchReaction).catch(() => {}), SEARCH_REACTION_AFTER_MS));
  if (writeReaction) timers.push(setTimeout(() => setStatus(writeReaction).catch(() => {}), WRITE_REACTION_AFTER_MS));

  return async (finalEmoji) => {
    stopped = true;
    for (const timer of timers) clearTimeout(timer);
    const previous = current;
    current = finalEmoji || current;
    if (previous && previous !== current) await removeOwnReaction(message, previous);
    if (current) {
      try {
        await message.react(current);
      } catch (err) {
        console.warn('final status reaction failed:', err?.message || err);
      }
    }
    for (const emoji of statusEmojis) {
      if (emoji !== current) await removeOwnReaction(message, emoji);
    }
  };
}

function startTypingLoop(channel) {
  let stopped = false;
  const send = () => {
    if (stopped) return;
    channel.sendTyping().catch(() => {});
  };
  send();
  const timer = setInterval(send, TYPING_REFRESH_MS);
  return () => {
    stopped = true;
    clearInterval(timer);
  };
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

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function isTransientLoreError(err) {
  const code = err?.cause?.code || err?.code || '';
  const message = String(err?.message || err?.cause?.message || '');
  return code === 'UND_ERR_SOCKET'
    || code === 'ECONNREFUSED'
    || code === 'ECONNRESET'
    || message.includes('fetch failed')
    || message.includes('terminated')
    || message.includes('HTTP 502')
    || message.includes('HTTP 503');
}

async function askLoreOnce(question, sessionContext) {
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

async function askLore(question, sessionContext) {
  const delays = [0, 1500, 3000, 5000];
  let lastError;
  for (let attempt = 0; attempt < delays.length; attempt += 1) {
    if (delays[attempt]) await sleep(delays[attempt]);
    try {
      return await askLoreOnce(question, sessionContext);
    } catch (err) {
      lastError = err;
      if (!isTransientLoreError(err) || attempt === delays.length - 1) throw err;
      console.warn(`lore answer transient failure; retrying (${attempt + 1}/${delays.length - 1}):`, err?.message || err);
    }
  }
  throw lastError;
}

client.once('clientReady', () => {
  console.log(`${displayName} logged in as ${client.user.tag}; watching channel ${channelId}`);
});

client.on('messageCreate', async (message) => {
  let finishStatus = null;
  try {
    if (message.author.bot) return;
    if (message.channelId !== channelId) return;
    if (!message.mentions.has(client.user)) return;

    const now = Date.now();
    const last = cooldowns.get(message.author.id) || 0;
    if (now - last < COOLDOWN_MS) {
      await message.reply({ content: appendAccuracyFooter(COOLDOWN_REPLY), allowedMentions: { repliedUser: false } });
      return;
    }
    cooldowns.set(message.author.id, now);

    const question = stripMention(message.content, client.user.id);
    if (!question) {
      await message.reply({ content: appendAccuracyFooter(EMPTY_REPLY), allowedMentions: { repliedUser: false } });
      return;
    }
    if (question.length > MAX_QUESTION_CHARS) {
      await message.reply({ content: appendAccuracyFooter(TOO_LONG_REPLY), allowedMentions: { repliedUser: false } });
      return;
    }

    const replyContext = await fetchReplyContext(message);
    const recentContext = pruneSession(message.channelId, now);
    const sessionContext = replyContext ? [...recentContext, replyContext] : recentContext;

    finishStatus = startStatusReactionSequence(message);
    const stopTyping = startTypingLoop(message.channel);
    const askStart = Date.now();
    let result;
    try {
      result = await askLore(question, sessionContext);
    } finally {
      stopTyping();
    }
    const elapsedMs = Date.now() - askStart;

    const baseAnswer = stripInlineCitations(sanitizeAnswer(result?.answer || ''));
    const withSources = result?.mode === 'archive' ? baseAnswer + formatSources(result) : baseAnswer;
    const finalAnswer = appendAccuracyFooter(withSources.trim() || ERROR_REPLY);

    logEvent({
      kind: 'agent_answer',
      user: message.author.username || message.author.id,
      channel: message.channelId,
      question,
      mode: result?.mode || 'unknown',
      route: result?.evidence?.route,
      confidence: result?.confidence,
      sources: (result?.sources || []).map((s) => s.title || s.source_title).slice(0, 8),
      candidate_count: result?.evidence?.candidate_count,
      elapsed_ms: elapsedMs,
      answer_preview: finalAnswer.slice(0, 240),
      context_messages: sessionContext.length,
    });

    rememberSessionMessage(message.channelId, 'User', question, client.user.id);
    rememberSessionMessage(
      message.channelId,
      'Librarian',
      stripAccuracyFooter(finalAnswer).replace(/\n\nSources:[\s\S]*$/i, ''),
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
        question_kind: classifyQuestionKind(question, result?.mode),
        mode: result?.mode,
        confidence: result?.confidence,
        elapsed_ms: elapsedMs,
        answer_preview: normalizeWhitespace(finalAnswer, 4000),
        answer_without_sources: normalizeWhitespace(baseAnswer, 3000),
        sources: (result?.sources || []).map((s) => s.title || s.source_title).slice(0, 8),
        source_details: compactSources(result?.sources),
        evidence: compactEvidence(result?.evidence),
      });
    }
    await finishStatus(doneReaction);
  } catch (err) {
    console.error('message handling failed:', err);
    logEvent({
      kind: 'agent_error',
      user: message.author?.username || message.author?.id,
      channel: message.channelId,
      question: stripMention(message.content || '', client.user?.id || ''),
      error: String(err?.message || err),
    });
    try {
      if (typeof finishStatus === 'function') await finishStatus(errorReaction);
    } catch {}
    await message.reply({
      content: appendAccuracyFooter(ERROR_REPLY),
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
    const record = botRepliesById.get(messageId) || loadBotReplyRecord(messageId);
    if (!record) return; // not a tracked bot reply

    const emoji = reaction.emoji?.name || reaction.emoji?.id || '?';
    const basePayload = {
      action,
      emoji,
      reaction_user: user?.username || user?.id,
      reaction_user_id: user?.id,
      bot_message_id: messageId,
      original_user: record.user,
      original_user_id: record.userId,
      channel: record.channel,
      question: record.question,
      question_kind: record.question_kind || classifyQuestionKind(record.question, record.mode),
      mode: record.mode,
      confidence: record.confidence,
      sources: record.sources,
    };

    logFeedback({
      kind: 'reaction',
      ...basePayload,
    });

    if (action === 'add' && isNegativeFeedbackEmoji(emoji)) {
      logNegativeFeedback({
        kind: 'negative_feedback',
        ...basePayload,
        answer_preview: record.answer_preview,
        answer_without_sources: record.answer_without_sources,
        source_details: record.source_details,
        evidence: record.evidence,
        elapsed_ms: record.elapsed_ms,
        audit_hint: 'A user marked this bot answer incorrect. Compare answer/source_details/evidence with the Drive archive and decide whether this was retrieval, interpretation, stale sync, missing data, or persona/banter handling.',
      });
    }

    if (action === 'add' && isAbstainFeedbackEmoji(emoji)) {
      logAbstainFeedback({
        kind: 'abstain_feedback',
        ...basePayload,
        answer_preview: record.answer_preview,
        answer_without_sources: record.answer_without_sources,
        source_details: record.source_details,
        evidence: record.evidence,
        elapsed_ms: record.elapsed_ms,
        audit_hint: 'A user marked this bot answer as partially correct, incomplete, or uncertain. Review whether the answer missed details, mixed sources, overclaimed, or answered the wrong part of the question.',
      });
    }
  } catch (err) {
    // Never let feedback handling crash anything.
    console.error('reaction handling failed:', err);
  }
}

client.on('messageReactionAdd', (reaction, user) => handleReaction(reaction, user, 'add'));
client.on('messageReactionRemove', (reaction, user) => handleReaction(reaction, user, 'remove'));

client.login(token);
