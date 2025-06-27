let context = #{};

// This generally comes from ANSWERS, but prompting for it ensures it is in the context 
context += prompt("Project Author:", "author_full", #{
    placeholder: "Your Name <your.name@example.com>",
});

context += prompt("Org Name:", "org-name", #{
  placeholder: "Acme",
  cased_as: [
    CasedIdentityCasedValue(PROGRAMMING_CASES),
    FixedKeyCasedValue("org-title", TitleCase),
  ],
  help: "Organization Name",
});

context += prompt("Solution Name:", "solution-name", #{
  placeholder: "Widgets",
  cased_as: [
    CasedIdentityCasedValue(PROGRAMMING_CASES),
    FixedKeyCasedValue("org-title", TitleCase),
  ],
  help: "Soltution Name",
});

context += prompt("Project Prefix:", "prefix-name", #{
  cased_as: [
    CasedIdentityCasedValue(PROGRAMMING_CASES),
    FixedKeyCasedValue("project-title", TitleCase),
  ],
  help: "Business Function",
});

context += prompt("Project Suffix:", "suffix-name", #{
  defaults_with: "Service",
  cased_as: [
    CasedIdentityCasedValue(PROGRAMMING_CASES),
    FixedKeyCasedValue("suffix-title", TitleCase),
  ],
  help: "Project Type",
});

render(Directory("contents/base"), context)
