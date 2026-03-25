#!/usr/bin/env node

const command = process.argv[2];
const args = process.argv.slice(3);

const COMMANDS = {
  install: '../src/commands/install-skills.js',
  list: '../src/commands/list-skills.js',
  sync: '../src/commands/sync-skills.js',
  setup: '../src/commands/setup-dependencies.js',
};

function printUsage() {
  console.log(`
claude-skillpack (csp) - Install Claude Code skills quickly

Usage:
  csp <command> [options]

Commands:
  install [name...]   Install all skills or specific ones to ~/.claude/skills/
  list                List available skills in the pack
  sync                Sync skills from ~/.claude/skills/ into this package (dev)
  setup               Install skills + run dependency installer

Options:
  --force             Overwrite existing skills without prompting
  --target <path>     Custom install target (default: ~/.claude/skills/)
  --help              Show this help message

Examples:
  npx csp install              # Install all skills
  npx csp install git debug    # Install specific skills
  npx csp list                 # List available skills
  npx csp setup               # Install skills + dependencies
`);
}

if (!command || command === '--help' || command === '-h') {
  printUsage();
  process.exit(0);
}

if (!COMMANDS[command]) {
  console.error(`Unknown command: "${command}". Run with --help for usage.`);
  process.exit(1);
}

// Load and run the command module
const commandModule = require(COMMANDS[command]);
commandModule(args);
