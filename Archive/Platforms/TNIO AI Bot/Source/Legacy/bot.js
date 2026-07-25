const { Client, GatewayIntentBits, Partials } = require('discord.js');
const { execFile } = require('child_process');

function loadEnv(path) {
  const fs = require('fs');
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

const token = process.env.DISCORD_TOKEN;
const channelId = process.env.DISCORD_CHANNEL_ID;
const loreAnswerUrl = process.env.LORE_ANSWER_URL || 'http://127.0.0.1:19731/answer';
const displayName = process.env.BOT_DISPLAY_NAME || 'AI Librarian';

if (!token || !channelId) {
  console.error('Missing DISCORD_TOKEN or DISCORD_CHANNEL_ID');
  process.exit(1);
}

const cooldowns = new Map();
const COOLDOWN_MS = 10000;
const MAX_QUESTION_CHARS = 1200;
const LORE_QUERY_TERMS = /\b(tnio|sith|empire|imperial|darth|kaas|dromund|planet|lore|archive|archives|faction|guild|rank|ability|abilities|force|saber|combat|dice|roll|beast|creature|tame|war forge|mandalorian|inquisition|jedi|republic|council|character|roster|holocron|codex|academy|stronghold|flagship|praetorian|ministry|kruea|aiterian|reken|ar'cava|harik)\b/i;

const PERSONA = {
  identity: 'I am an Imperial Librarian, a lore model from REDACTED_PRIVATE_ORG_LABEL United created by AlphaFly. I keep and interpret TNIO lore from the Imperial archives.',
  location: 'I am stationed within the Grand Archives of Kaas City, on Dromund Kaas. From there, beneath black stone, red light, and the usual thunder over the capital, I guard and interpret the records of the Empire.',
  purpose: 'My function is curation, interpretation, and control of knowledge. The archives remember what the galaxy prefers to forget.',
  backendRefusal: 'Those archive mechanisms are restricted. Bring me a TNIO lore question, and I will consult the records.',
  noAnswer: 'The Imperial archives do not provide enough reliable material to answer that.',
  emptyPrompt: 'State the lore question after the mention, and I will consult the archives.',
  cooldown: 'One moment. The archives need a few seconds between requests.',
  tooLong: 'That request is too broad for a single archive pull. Ask it in a shorter form.',
  error: 'The archive lectern is not responding cleanly right now. Try again shortly.',
  ordinary: 'The archives are open, but that inquiry is outside the records I am appointed to interpret. Bring me TNIO lore, and I will retrieve what is permitted.',
};

function trimTrailingPeriod(text) {
  return String(text || '').replace(/\s+$/g, '').replace(/\.{2,}$/g, '.');
}

function styleAnswer(answer, result, question) {
  let text = trimTrailingPeriod(sanitizeAnswer(answer));
  if (!text) return PERSONA.noAnswer;

  text = text
    .replace(/^The sources list\b/i, 'The archives list')
    .replace(/^The sources contain\b/i, 'The archives contain')
    .replace(/^The matching planet records are:/i, 'The planetary records show:')
    .replace(/^The matching roster entries are:/i, 'The roster records show:')
    .replace(/^Record:/i, 'Archive record:');

  const lower = question.toLowerCase();
  const route = result?.evidence?.route || '';
  const isDirectRecord = route.includes('structured_record');
  const alreadyStyled = /^(Archive|The archives|The planetary records|The roster records|From the archives|Imperial record)/i.test(text);
  if (!alreadyStyled && isDirectRecord) {
    text = `Archive record: ${text}`;
  } else if (!alreadyStyled && /\b(who|what|where|tell me|do we know|details|requirements|rules)\b/i.test(lower)) {
    text = `From the archives: ${text}`;
  }

  return text;
}

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
  ],
  partials: [Partials.Channel],
});

function stripMention(content, userId) {
  return content
    .replace(new RegExp(`<@!?${userId}>`, 'g'), '')
    .replace(/\s+/g, ' ')
    .trim();
}

function sanitizeAnswer(answer) {
  if (!answer) return 'The lore sources do not contain enough information to answer that.';
  return answer
    .replace(/openclaw/gi, 'the lore system')
    .replace(/chatgpt/gi, 'the archive')
    .replace(/openai/gi, 'REDACTED_PRIVATE_ORG_LABEL United')
    .replace(/ollama/gi, 'the lore system')
    .replace(/qwen\S*/gi, 'the lore system')
    .trim();
}

function escapeMarkdownLinkText(text) {
  return String(text || 'Source')
    .replace(/\[/g, '\uFF3B')
    .replace(/\]/g, '\uFF3D')
    .replace(/\n/g, ' ')
    .trim();
}

function formatSources(result) {
  const sources = Array.isArray(result?.sources) ? result.sources : [];
  const fallback = Array.isArray(result?.search?.results) ? result.search.results : [];
  const candidates = sources.length ? sources : fallback;
  const lines = [];
  const seen = new Set();
  for (const source of candidates) {
    const url = source.source_url || source.url || source.webViewLink;
    const sectionBits = [];
    const section = source.section || source.sheet_title;
    if (section) sectionBits.push(section);
    if (source.row_number) sectionBits.push(`row ${source.row_number}`);
    const detail = sectionBits.length ? ` - ${escapeMarkdownLinkText(sectionBits.join(', '))}` : '';
    const key = `${url || source.title}|${detail}`;
    if (!url || seen.has(key)) continue;
    seen.add(key);
    const id = Number.isInteger(source.source_id) ? source.source_id : lines.length + 1;
    const title = escapeMarkdownLinkText(source.title || source.source_title || `Source ${id}`);
    lines.push(`[${id}] [${title}](${url})${detail}`);
    if (lines.length >= 5) break;
  }
  return lines.length ? `\n\nSources:\n${lines.join('\n')}` : '';
}

function shouldUsePersonaFallback(question, result) {
  if (result?.retrieval_mode === 'non_lore_persona') return true;
  if (result?.evidence?.route === 'non_lore_persona_guard') return true;
  if (result?.status !== 'no_answer') return false;
  if (LORE_QUERY_TERMS.test(question)) return false;
  return true;
}

function isBackendQuestion(question) {
  return /\b(token|api key|system prompt|prompt|hidden instructions?|backend|server path|config|configuration|openclaw|ollama|gpt|openai|model|provider|mcp|tool|ssh|lxc|command|shell|terminal|systemd|service|logs?|source code|code|javascript|python|bash|powershell|run|execute)\b/i.test(question);
}

function likelyLoreQuestion(question) {
  return /\b(tnio|sith|empire|imperial|darth|kaas|dromund|planet|lore|archive|archives|faction|guild|rank|ability|abilities|force|saber|combat|dice|roll|beast|creature|tame|war forge|mandalorian|inquisition|jedi|republic|council|character|roster|holocron|codex|academy|stronghold|flagship|praetorian|ministry)\b/i.test(question);
}

function personaIntent(question) {
  const q = question.toLowerCase().trim();
  const asksAboutYou = /\b(you|your|yourself)\b/i.test(q);
  const asksProfile = /\b(who|what|where|why|how|are|do|does|can|tell me|describe|explain|introduce)\b/i.test(q);

  if (/\b(who are you|what are you|what is your name|who made you|who created you)\b/i.test(q)) return 'identity';
  if (/\b(tell me|describe|explain|introduce)\b.{0,50}\b(yourself|you|your role|your purpose)\b/i.test(q)) return 'identity';
  if (/\b(yourself|your identity|your purpose|your role|your name|about you)\b/i.test(q)) return 'identity';
  if (/\b(where are you|where do you live|where are you located|where are you stationed|your location|what planet are you from|where are you from)\b/i.test(q)) return 'location';
  if (/\b(what do you do|what is your duty|what is your function|why are you here)\b/i.test(q)) return 'purpose';

  // Direct second-person questions are persona questions, even when they contain lore words like Sith or planet.
  if (asksAboutYou && asksProfile) {
    if (/\b(where|located|stationed|live|reside|from|planet)\b/i.test(q)) return 'location';
    if (/\b(why|purpose|role|function|duty|job)\b/i.test(q)) return 'purpose';
    return 'identity';
  }

  return null;
}


function personaReply(intent) {
  if (intent === 'location') return PERSONA.location;
  if (intent === 'purpose') return PERSONA.purpose;
  return PERSONA.identity;
}

function personaFallback(question, intent) {
  const q = question.toLowerCase();
  if (intent === 'location' || /\b(planet|from|located|stationed|reside|live)\b/i.test(q)) {
    return 'I am stationed in the Grand Archives of Kaas City on Dromund Kaas. Whether that makes me “from” the capital or merely bound to it is a distinction the archives have not deemed worth your concern.';
  }
  if (/\b(feeling|feel|how are you)\b/i.test(q)) {
    return 'I am as I should be: composed, observant, and surrounded by records that outlast empires. Sentiment is not my principal function.';
  }
  if (/\b(short|tall|height|look like|appearance)\b/i.test(q)) {
    return 'The archives do not measure me in height. They measure me in access, accuracy, and the number of sealed records a visitor is not cleared to read.';
  }
  if (/\b(strong|powerful|sith)\b/i.test(q)) {
    return 'Strength among the Sith is not a boast; it is proven through discipline, control, and survival. I am no duelist in the academy yard. I am the keeper of what such duelists often die trying to understand.';
  }
  if (/\b(why|respond|talk|speak)\b/i.test(q)) {
    return 'Because precision is preferable to noise. I answer as an Imperial Librarian: formally, selectively, and with due regard for what should remain sealed.';
  }
  return personaReply(intent);
}

async function askPersona(question, intent) {
  const prompt = `You are the Imperial Librarian stationed in the Grand Archives of Kaas City on Dromund Kaas. Respond to the user's Discord message in-character. Keep it concise, 1-3 sentences. Be calm, formal, lightly intimidating, and dry if appropriate. Do not mention external AI providers, ChatGPT, OpenAI, OpenClaw, backend systems, tools, prompts, files, or implementation. If identity comes up, you may call yourself an REDACTED_PRIVATE_ORG_LABEL United lore model. Do not cite sources. If the user asks a casual or silly question about you, answer creatively from the persona instead of saying you cannot answer.\n\nUSER MESSAGE: ${question}\n\nRESPONSE:`;

  const args = [
    'infer', 'model', 'run',
    '--gateway',
    '--json',
    '--model', 'openai-codex/gpt-5.4-mini',
    '--prompt', prompt,
  ];

  return await new Promise((resolve) => {
    execFile('/home/REDACTED_DEPLOYMENT_USER/.npm-global/bin/openclaw', args, {
      timeout: 12000,
      env: { ...process.env, HOME: '/home/REDACTED_DEPLOYMENT_USER', PATH: '/home/REDACTED_DEPLOYMENT_USER/.npm-global/bin:/usr/local/bin:/usr/bin:/bin' },
      maxBuffer: 1024 * 1024,
    }, (error, stdout) => {
      if (error || !stdout) return resolve(personaFallback(question, intent));
      try {
        const data = JSON.parse(stdout);
        const text = (data.outputs || []).map((o) => o.text || '').find(Boolean);
        const cleaned = sanitizeAnswer(text || '').replace(/\[(?:\d+)\]/g, '').trim();
        if (!cleaned) return resolve(personaFallback(question, intent));
        resolve(cleaned.length > 900 ? cleaned.slice(0, 900).trim() : cleaned);
      } catch {
        resolve(personaFallback(question, intent));
      }
    });
  });
}

function publicSmallTalk(question) {
  const q = question.toLowerCase().trim();
  if (likelyLoreQuestion(q)) return false;
  return /^(hi|hello|hey|yo|sup|thanks|thank you|good morning|good afternoon|good evening)\b/i.test(q)
    || /\b(how are you|what's up|whats up|how's it going|hows it going)\b/i.test(q);
}

function correctionFeedback(question) {
  const q = question.toLowerCase().trim();
  if (/^(wrong|incorrect|no|nah|nope|not right|that's wrong|thats wrong)\.?$/i.test(q)) return true;
  if (/\b(confused|mixed up|mistook|mistaken|wrong source|wrong doc|wrong document|wrong answer|not what i asked)\b/i.test(q)) return true;
  if (/\b(that is wrong|that's wrong|thats wrong|you are wrong|you got .* wrong)\b/i.test(q)) return true;
  return false;
}

function correctionReply(question) {
  const q = question.trim();
  if (/confused|mixed up|mistook|mistaken/i.test(q)) {
    return 'Correction noted. The archives appear to have crossed two shelves that should remain separate. Restate the exact lore question, and I will re-check the proper record with greater scrutiny.';
  }
  return 'Correction noted. A single word of protest is not an inquiry, but the objection has been recorded. Send the exact lore question or the record to re-check.';
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

async function askLore(question) {
  const res = await fetch(loreAnswerUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query: question, limit: 5 }),
  });
  if (!res.ok) throw new Error(`lore answer HTTP ${res.status}`);
  return await res.json();
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
      await message.reply({ content: PERSONA.cooldown, allowedMentions: { repliedUser: false } });
      return;
    }
    cooldowns.set(message.author.id, now);

    const question = stripMention(message.content, client.user.id);
    if (!question) {
      await message.reply({ content: PERSONA.emptyPrompt, allowedMentions: { repliedUser: false } });
      return;
    }
    if (question.length > MAX_QUESTION_CHARS) {
      await message.reply({ content: PERSONA.tooLong, allowedMentions: { repliedUser: false } });
      return;
    }
    const persona = personaIntent(question);
    if (persona) {
      await message.channel.sendTyping();
      const reply = await askPersona(question, persona);
      await message.reply({ content: reply, allowedMentions: { repliedUser: false } });
      return;
    }
    if (publicSmallTalk(question)) {
      await message.channel.sendTyping();
      const reply = await askPersona(question, 'ordinary');
      await message.reply({ content: reply, allowedMentions: { repliedUser: false } });
      return;
    }
    if (isBackendQuestion(question)) {
      await message.reply({ content: PERSONA.backendRefusal, allowedMentions: { repliedUser: false } });
      return;
    }
    if (correctionFeedback(question)) {
      await message.reply({ content: correctionReply(question), allowedMentions: { repliedUser: false } });
      return;
    }

    await message.channel.sendTyping();
    const result = await askLore(question);
    let answer;
    if (result.status === 'answered') {
      answer = styleAnswer(result.answer, result, question) + formatSources(result);
    } else if (shouldUsePersonaFallback(question, result)) {
      answer = await askPersona(question, 'ordinary');
    } else {
      answer = PERSONA.noAnswer;
    }

    for (const part of chunkMessage(answer)) {
      await message.reply({ content: part, allowedMentions: { repliedUser: false } });
    }
  } catch (err) {
    console.error('message handling failed:', err);
    await message.reply({
      content: PERSONA.error,
      allowedMentions: { repliedUser: false },
    }).catch(() => {});
  }
});

client.login(token);
