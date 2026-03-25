const fs = require('fs');
const path = require('path');
const { SKILLS_DIR, PACKAGE_SKILLS_DIR, getAvailableSkills, copySkill, copyFile } = require('../utils');

/** Top-level files to copy alongside skill directories */
const TOP_LEVEL_FILES = ['install.sh', 'install.ps1', 'INSTALLATION.md', 'README.md', 'THIRD_PARTY_NOTICES.md'];

/**
 * Parse CLI flags from args array.
 * Returns { force, target, skillNames }
 */
function parseArgs(args) {
  let force = false;
  let target = SKILLS_DIR;
  const skillNames = [];

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--force' || args[i] === '-f') {
      force = true;
    } else if (args[i] === '--target' || args[i] === '-t') {
      target = args[++i];
    } else if (!args[i].startsWith('-')) {
      skillNames.push(args[i]);
    }
  }

  return { force, target, skillNames };
}

/**
 * Install skills to target directory.
 * @param {string[]} args - CLI arguments
 */
module.exports = function installSkills(args) {
  const { force, target, skillNames } = parseArgs(args);
  const available = getAvailableSkills();

  if (available.length === 0) {
    console.error('No skills found in package. Run "claude-skillpack sync" first to bundle skills.');
    process.exit(1);
  }

  // Determine which skills to install
  const toInstall = skillNames.length > 0
    ? skillNames.filter(name => {
        if (!available.includes(name)) {
          console.warn(`  Warning: skill "${name}" not found in pack, skipping.`);
          return false;
        }
        return true;
      })
    : available;

  if (toInstall.length === 0) {
    console.error('No valid skills to install.');
    process.exit(1);
  }

  // Ensure target directory exists
  fs.mkdirSync(target, { recursive: true });

  console.log(`Installing ${toInstall.length} skill(s) to ${target}...\n`);

  let installed = 0;
  let skipped = 0;

  for (const skill of toInstall) {
    const destPath = path.join(target, skill);
    const exists = fs.existsSync(destPath);

    if (exists && !force) {
      // Overwrite by default but log it
      console.log(`  Updating: ${skill}`);
    } else if (!exists) {
      console.log(`  Installing: ${skill}`);
    } else {
      console.log(`  Overwriting: ${skill}`);
    }

    try {
      copySkill(skill, PACKAGE_SKILLS_DIR, target);
      installed++;
    } catch (err) {
      console.error(`  Failed: ${skill} - ${err.message}`);
      skipped++;
    }
  }

  // Copy top-level files (install.sh, README, etc.)
  if (skillNames.length === 0) {
    for (const file of TOP_LEVEL_FILES) {
      if (copyFile(file, PACKAGE_SKILLS_DIR, target)) {
        console.log(`  Copied: ${file}`);
      }
    }
  }

  console.log(`\nDone! ${installed} installed, ${skipped} failed.`);

  if (installed > 0 && skillNames.length === 0) {
    console.log('\nRun "claude-skillpack setup" to install dependencies (Python venv, system tools).');
  }
};
