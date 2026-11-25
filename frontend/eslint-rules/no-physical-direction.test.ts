import { RuleTester } from "eslint";
import { describe, it } from "vitest";
import rule from "./no-physical-direction.mjs";

RuleTester.describe = describe;
RuleTester.it = it;

const ruleTester = new RuleTester({
  languageOptions: {
    ecmaVersion: 2024,
    sourceType: "module",
    parserOptions: { ecmaFeatures: { jsx: true } },
  },
});

const err = (found: string, suggestion: string) => ({
  messageId: "physicalClass",
  data: { found, suggestion },
});

ruleTester.run("no-physical-direction", rule, {
  valid: [
    {
      code: '<div className="ms-4 pe-2 text-start border-s-2 rounded-e-lg dark:ms-4 hover:pe-2 md:text-start start-0 end-[3px]" />',
    },
    {
      code: '<div style={{ marginInlineStart: 8, textAlign: "start", float: "inline-end" }} />',
    },
    {
      // RuleTester registers the rule under "rule-to-test/"; the real config uses "local/".
      code: '<div className="ml-4" /> // eslint-disable-line rule-to-test/no-physical-direction -- legend swatch is intentionally LTR-fixed',
    },
  ],
  invalid: [
    {
      code: '<div className="ml-4 pr-2 text-right left-0 float-left border-r-2 rounded-r-lg" />',
      errors: [
        err("ml-4", "ms-4"),
        err("pr-2", "pe-2"),
        err("text-right", "text-end"),
        err("left-0", "start-0"),
        err("float-left", "float-start"),
        err("border-r-2", "border-e-2"),
        err("rounded-r-lg", "rounded-e-lg"),
      ],
    },
    {
      // Stacked variants, arbitrary variants/values, negatives and the important marker need no hardcoded variant list.
      code: '<div className="dark:ml-4 md:hover:pr-2 [&:hover]:mr-4 right-[3px] md:-ml-4 ml-4!" />',
      errors: [
        err("dark:ml-4", "dark:ms-4"),
        err("md:hover:pr-2", "md:hover:pe-2"),
        err("[&:hover]:mr-4", "[&:hover]:me-4"),
        err("right-[3px]", "end-[3px]"),
        err("md:-ml-4", "md:-ms-4"),
        err("ml-4!", "ms-4!"),
      ],
    },
    {
      code: "<div className={`pr-2 ${extra}`} />",
      errors: [err("pr-2", "pe-2")],
    },
    {
      code: 'cn("ml-4", isActive && "text-right"); clsx({ "pl-2": isOpen });',
      errors: [
        err("ml-4", "ms-4"),
        err("text-right", "text-end"),
        err("pl-2", "ps-2"),
      ],
    },
    {
      code: '<div style={{ marginLeft: 8, right: 0, borderRight: "1px solid", textAlign: "left", float: "right" }} />',
      errors: [
        {
          messageId: "physicalStyleProp",
          data: { found: "marginLeft", suggestion: "marginInlineStart" },
        },
        {
          messageId: "physicalStyleProp",
          data: { found: "right", suggestion: "insetInlineEnd" },
        },
        {
          messageId: "physicalStyleProp",
          data: { found: "borderRight", suggestion: "borderInlineEnd" },
        },
        {
          messageId: "physicalStyleValue",
          data: { found: "textAlign", value: "left", suggestion: "start" },
        },
        {
          messageId: "physicalStyleValue",
          data: { found: "float", value: "right", suggestion: "inline-end" },
        },
      ],
    },
  ],
});
