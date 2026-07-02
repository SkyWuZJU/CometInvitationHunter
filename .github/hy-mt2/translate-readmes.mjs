// Managed by hy-mt2-github-translator. Do not edit by hand; regenerate instead.
// Zero-dependency README translator using Node.js 20 built-ins and Tencent Hunyuan MT.
import { readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(scriptDir, "..", "..");
const config = JSON.parse(await readFile(path.join(scriptDir, "config.json"), "utf8"));

const apiKey = process.env[config.apiKeyEnv];
if (!apiKey) {
  throw new Error("Missing translation API key: set the " + config.apiKeyEnv + " secret in the repository settings.");
}

const rawSource = await readFile(path.join(repoRoot, config.sourceReadme), "utf8");
const source = stripManagedBlock(rawSource, config.managedBlock);

for (const target of config.targets) {
  const prompt = buildPrompt(config.sourceReadme, target.label, source);
  const content = await translate(prompt, config, apiKey);
  await writeFile(path.join(repoRoot, target.path), ensureTrailingNewline(content), "utf8");
  console.log("Translated " + config.sourceReadme + " -> " + target.path + " (" + target.language + ")");
}

function stripManagedBlock(content, managedBlock) {
  if (!managedBlock || !managedBlock.start || !managedBlock.end) {
    return content;
  }
  const pattern = new RegExp(escapeRegExp(managedBlock.start) + "[\\s\\S]*?" + escapeRegExp(managedBlock.end) + "\\n*", "g");
  return content.replace(pattern, "");
}

function buildPrompt(sourcePath, targetLabel, content) {
  return [
    "请将以下 Markdown README 文件翻译为" + targetLabel + "。",
    "",
    "翻译规则：",
    "- 只输出翻译后的 Markdown 正文。",
    "- 保留 Markdown 结构、标题层级、表格、链接、URL、徽章、代码块、行内代码、命令示例、占位符和文件路径。",
    "- 翻译正文、标题、说明文字和表格文本中适合翻译的自然语言内容。",
    "- 项目名、API 名、包名、模型名、标识符和代码符号保持原文，除非原文已经给出对应译名。",
    "- 不要添加解释，不要用额外代码围栏包裹结果。",
    "",
    "源文件：" + sourcePath,
    "",
    "Markdown 内容：",
    content
  ].join("\n");
}

async function translate(prompt, config, apiKey) {
  const url = config.baseUrl.replace(/\/+$/, "") + "/chat/completions";
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Authorization": "Bearer " + apiKey,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      model: config.model,
      messages: [{ role: "user", content: prompt }]
    })
  });

  if (!response.ok) {
    const errorBody = await response.text().catch(() => "");
    throw new Error("Translation request failed with HTTP " + response.status + ": " + (errorBody || response.statusText));
  }

  const parsed = await response.json();
  const content = parsed && parsed.choices && parsed.choices[0] && parsed.choices[0].message && parsed.choices[0].message.content;
  if (typeof content !== "string" || content.trim().length === 0) {
    throw new Error("Translation response did not include message content.");
  }
  return content;
}

function ensureTrailingNewline(content) {
  return content.endsWith("\n") ? content : content + "\n";
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
