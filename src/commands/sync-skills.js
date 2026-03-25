const fs = require('fs');
const path = require('path');
const { SKILLS_DIR, PACKAGE_SKILLS_DIR, getInstalledSkills, copySkill, copyFile } = require('../utils');

/** Top-level files to sync from source skills directory */
const TOP_LEVEL_FILES = ['install.sh', 'install.ps1', 'INSTALLATION.md', 'README.md', 'THIRD_PARTY_NOTICES.md'];

/** Directories/patterns to skip when syncing (runtime artifacts, not skill source) */
const SKIP_DIRS = new Set(['.venv', 'node_modules', '__pycache__', '.git']);

/**
 * Sync skills from ~/.claude/skills/ into this package's skills/ directory.
 * Used during development to update bundled skills.
 * @param {string[]} args - CLI arguments
 */
module.exports = function syncSkills(args) {
  let source = SKILLS_DIR;
  let excludePatterns = [];

  // Parse args
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--source' || args[i] === '-s') {
      source = args[++i];
    } else if (args[i] === '--exclude') {
      excludePatterns.push(args[++i]);
    }
  }

  if (!fs.existsSync(source)) {
    console.error(`Source directory not found: ${source}`);
    process.exit(1);
  }

  const skills = getInstalledSkills(source);
  const excludeSet = new Set(excludePatterns);

  // Filter out non-skill directories and excluded
  const toSync = skills.filter(name => {
    if (SKIP_DIRS.has(name)) return false;
    if (excludeSet.has(name)) return false;
    // Must contain SKILL.md to be a valid skill
    const skillMd = path.join(source, name, 'SKILL.md');
    return fs.existsSync(skillMd);
  });

  console.log(`Syncing ${toSync.length} skill(s) from ${source} to package...\n`);

  // Ensure target exists
  fs.mkdirSync(PACKAGE_SKILLS_DIR, { recursive: true });

  let synced = 0;
  for (const skill of toSync) {
    try {
      copySkillFiltered(skill, source, PACKAGE_SKILLS_DIR);
      console.log(`  Synced: ${skill}`);
      synced++;
    } catch (err) {
      console.error(`  Failed: ${skill} - ${err.message}`);
    }
  }

  // Copy top-level files
  for (const file of TOP_LEVEL_FILES) {
    if (copyFile(file, source, PACKAGE_SKILLS_DIR)) {
      console.log(`  Copied: ${file}`);
    }
  }

  console.log(`\nDone! ${synced}/${toSync.length} skills synced.`);
};

/**
 * Copy a skill directory, filtering out runtime artifacts.
 * Skips .venv, node_modules, __pycache__, .pyc files.
 */
function copySkillFiltered(skillName, srcBase, destBase) {
  const src = path.join(srcBase, skillName);
  const dest = path.join(destBase, skillName);

  fs.cpSync(src, dest, {
    recursive: true,
    force: true,
    filter: (srcPath) => {
      const basename = path.basename(srcPath);
      // Skip runtime artifact directories and files
      if (SKIP_DIRS.has(basename)) return false;
      if (basename.endsWith('.pyc')) return false;
      if (basename === '.env') return false;
      return true;
    },
  });
}
