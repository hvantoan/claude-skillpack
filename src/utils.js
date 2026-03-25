const fs = require('fs');
const path = require('path');
const os = require('os');

/** Default target directory for skills installation */
const SKILLS_DIR = path.join(os.homedir(), '.claude', 'skills');

/** Source skills directory within this package */
const PACKAGE_SKILLS_DIR = path.join(__dirname, '..', 'skills');

/**
 * Get list of all skill names bundled in the package.
 * Each skill is a directory containing a SKILL.md file.
 */
function getAvailableSkills() {
  if (!fs.existsSync(PACKAGE_SKILLS_DIR)) return [];
  return fs.readdirSync(PACKAGE_SKILLS_DIR, { withFileTypes: true })
    .filter(d => d.isDirectory())
    .map(d => d.name)
    .sort();
}

/**
 * Get list of skills currently installed at target directory.
 */
function getInstalledSkills(targetDir = SKILLS_DIR) {
  if (!fs.existsSync(targetDir)) return [];
  return fs.readdirSync(targetDir, { withFileTypes: true })
    .filter(d => d.isDirectory())
    .map(d => d.name)
    .sort();
}

/**
 * Copy a single skill directory from source to destination.
 * Uses fs.cpSync for recursive copy (Node 16.7+).
 */
function copySkill(skillName, srcBase, destBase) {
  const src = path.join(srcBase, skillName);
  const dest = path.join(destBase, skillName);

  if (!fs.existsSync(src)) {
    throw new Error(`Skill "${skillName}" not found in ${srcBase}`);
  }

  fs.cpSync(src, dest, { recursive: true, force: true });
}

/**
 * Copy a single file from source to destination directory.
 */
function copyFile(fileName, srcBase, destBase) {
  const src = path.join(srcBase, fileName);
  const dest = path.join(destBase, fileName);

  if (!fs.existsSync(src)) return false;
  fs.copyFileSync(src, dest);
  return true;
}

module.exports = {
  SKILLS_DIR,
  PACKAGE_SKILLS_DIR,
  getAvailableSkills,
  getInstalledSkills,
  copySkill,
  copyFile,
};
