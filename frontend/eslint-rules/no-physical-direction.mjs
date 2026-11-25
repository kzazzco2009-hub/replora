// Bans physical-direction CSS (Tailwind utilities and style properties) so layouts stay RTL-safe. See docs/design.md §4/§7.

const CLASS_SUGGESTIONS = {
  ml: "ms",
  mr: "me",
  pl: "ps",
  pr: "pe",
  left: "start",
  right: "end",
  "border-l": "border-s",
  "border-r": "border-e",
  "rounded-l": "rounded-s",
  "rounded-r": "rounded-e",
  "float-left": "float-start",
  "float-right": "float-end",
  "scroll-ml": "scroll-ms",
  "scroll-mr": "scroll-me",
  "text-left": "text-start",
  "text-right": "text-end",
};

const ALWAYS_BANNED_STYLE_PROPS = {
  marginLeft: "marginInlineStart",
  marginRight: "marginInlineEnd",
  paddingLeft: "paddingInlineStart",
  paddingRight: "paddingInlineEnd",
  left: "insetInlineStart",
  right: "insetInlineEnd",
  borderLeft: "borderInlineStart",
  borderRight: "borderInlineEnd",
};

const VALUE_BANNED_STYLE_PROPS = {
  textAlign: { left: "start", right: "end" },
  float: { left: "inline-start", right: "inline-end" },
};

const CLASS_HELPER_NAMES = new Set([
  "clsx",
  "cn",
  "classnames",
  "classNames",
  "cva",
  "twMerge",
  "twJoin",
]);

// Splits variant prefix (up to the last top-level `:`, bracket-depth tracked so no variant list is needed), then markers, then the base utility.
function splitToken(token) {
  let depth = 0;
  let lastColon = -1;
  for (let i = 0; i < token.length; i += 1) {
    const char = token[i];
    if (char === "[") depth += 1;
    else if (char === "]") depth -= 1;
    else if (char === ":" && depth === 0) lastColon = i;
  }
  const variantPrefix = lastColon === -1 ? "" : token.slice(0, lastColon + 1);
  let rest = lastColon === -1 ? token : token.slice(lastColon + 1);
  const importantLeading = rest.startsWith("!");
  if (importantLeading) rest = rest.slice(1);
  const importantTrailing = rest.endsWith("!");
  if (importantTrailing) rest = rest.slice(0, -1);
  const negative = rest.startsWith("-");
  if (negative) rest = rest.slice(1);
  return {
    variantPrefix,
    importantLeading,
    importantTrailing,
    negative,
    base: rest,
  };
}

function rebuildToken(p, replacement) {
  return `${p.variantPrefix}${p.importantLeading ? "!" : ""}${p.negative ? "-" : ""}${replacement}${p.importantTrailing ? "!" : ""}`;
}

function findClassSuggestion(token) {
  const parts = splitToken(token);
  for (const [key, replacement] of Object.entries(CLASS_SUGGESTIONS)) {
    if (parts.base === key || parts.base.startsWith(`${key}-`)) {
      const remainder = parts.base.slice(key.length);
      return rebuildToken(parts, `${replacement}${remainder}`);
    }
  }
  return null;
}

function collectClassStrings(expr, out) {
  if (!expr) return;
  switch (expr.type) {
    case "Literal":
      if (typeof expr.value === "string")
        out.push({ node: expr, text: expr.value });
      break;
    case "TemplateLiteral":
      for (const quasi of expr.quasis) {
        if (quasi.value.raw) out.push({ node: quasi, text: quasi.value.raw });
      }
      break;
    case "ConditionalExpression":
      collectClassStrings(expr.consequent, out);
      collectClassStrings(expr.alternate, out);
      break;
    case "LogicalExpression":
      collectClassStrings(expr.left, out);
      collectClassStrings(expr.right, out);
      break;
    case "ArrayExpression":
      for (const element of expr.elements) collectClassStrings(element, out);
      break;
    case "ObjectExpression":
      for (const prop of expr.properties) {
        if (prop.type !== "Property" || prop.computed) continue;
        const key =
          prop.key.type === "Identifier" ? prop.key.name : prop.key.value;
        if (typeof key === "string") out.push({ node: prop.key, text: key });
      }
      break;
    default:
      break;
  }
}

function checkStyleExpression(context, expr) {
  if (!expr) return;
  if (expr.type === "ConditionalExpression") {
    checkStyleExpression(context, expr.consequent);
    checkStyleExpression(context, expr.alternate);
    return;
  }
  if (expr.type !== "ObjectExpression") return;

  for (const prop of expr.properties) {
    if (prop.type !== "Property" || prop.computed) continue;
    const keyName =
      prop.key.type === "Identifier" ? prop.key.name : prop.key.value;
    if (typeof keyName !== "string") continue;

    if (keyName in ALWAYS_BANNED_STYLE_PROPS) {
      context.report({
        node: prop.key,
        messageId: "physicalStyleProp",
        data: {
          found: keyName,
          suggestion: ALWAYS_BANNED_STYLE_PROPS[keyName],
        },
      });
      continue;
    }

    if (keyName in VALUE_BANNED_STYLE_PROPS) {
      const value = prop.value;
      if (value.type === "Literal" && typeof value.value === "string") {
        const direction = value.value.trim().toLowerCase();
        const suggestion = VALUE_BANNED_STYLE_PROPS[keyName][direction];
        if (suggestion) {
          context.report({
            node: prop.value,
            messageId: "physicalStyleValue",
            data: { found: keyName, value: direction, suggestion },
          });
        }
      }
    }
  }
}

/** @type {import("eslint").Rule.RuleModule} */
const rule = {
  meta: {
    type: "problem",
    docs: { description: "Logical CSS only; keeps layouts RTL-safe." },
    schema: [],
    messages: {
      physicalClass:
        'Physical-direction Tailwind class "{{found}}" breaks RTL layouts. Use "{{suggestion}}" instead.',
      physicalStyleProp:
        'Physical-direction style property "{{found}}" breaks RTL layouts. Use "{{suggestion}}" instead.',
      physicalStyleValue:
        'Physical-direction value "{{found}}: {{value}}" breaks RTL layouts. Use "{{found}}: {{suggestion}}" instead.',
    },
  },
  create(context) {
    function scanClassText(node, text) {
      for (const token of text.split(/\s+/).filter(Boolean)) {
        const suggestion = findClassSuggestion(token);
        if (suggestion) {
          context.report({
            node,
            messageId: "physicalClass",
            data: { found: token, suggestion },
          });
        }
      }
    }

    function scanHelperArgs(args) {
      const strings = [];
      for (const arg of args) collectClassStrings(arg, strings);
      for (const { node: stringNode, text } of strings)
        scanClassText(stringNode, text);
    }

    return {
      CallExpression(node) {
        if (
          node.callee.type === "Identifier" &&
          CLASS_HELPER_NAMES.has(node.callee.name)
        ) {
          scanHelperArgs(node.arguments);
        }
      },
      JSXAttribute(node) {
        const attrName = node.name.name;
        const value = node.value;
        if (
          attrName === "className" &&
          value?.type === "Literal" &&
          typeof value.value === "string"
        ) {
          scanClassText(value, value.value);
        } else if (
          attrName === "className" &&
          value?.type === "JSXExpressionContainer"
        ) {
          scanHelperArgs([value.expression]);
        } else if (
          attrName === "style" &&
          value?.type === "JSXExpressionContainer"
        ) {
          checkStyleExpression(context, value.expression);
        }
      },
    };
  },
};

export default rule;
