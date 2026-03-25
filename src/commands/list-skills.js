const fs = require('fs');
const path = require('path');
const { PACKAGE_SKILLS_DIR, SKILLS_DIR, getAvailableSkills, getInstalledSkills } = require('../utils');

/**
 * List available skills in the pack with install status.
 * @param {string[]} args - CLI arguments
 */
module.exports = function listSkills(args) {
  const available = getAvailableSkills();
  const installed = getInstalledSkills();
  const installedSet = new Set(installed);

  if (available.length === 0) {
    console.log('No skills bundled in package. Run "claude-skillpack sync" to bundle skills.');
    return;
  }

  console.log(`\nAvailable skills (${available.length}):\n`);

  // Read SKILL.md first line for description
  for (const skill of available) {
    const status = installedSet.has(skill) ? '[installed]' : '[not installed]';
    const description = getSkillDescription(skill);
    const desc = description ? ` - ${description}` : '';
    console.log(`  ${status.padEnd(16)} ${skill}${desc}`);
  }

  console.log(`\nInstall target: ${SKILLS_DIR}`);
  console.log(`Total: ${available.length} available, ${installed.length} installed\n`);
};

/**
 * Extract first meaningful line from SKILL.md as description.
 */
function getSkillDescription(skillName) {
  const skillMd = path.join(PACKAGE_SKILLS_DIR, skillName, 'SKILL.md');
  if (!fs.existsSync(skillMd)) return '';

  try {
    const content = fs.readFileSync(skillMd, 'utf-8');
    const lines = content.split('\n');

    // Find first non-empty, non-heading line
    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed && !trimmed.startsWith('#') && !trimmed.startsWith('---')) {
        // Truncate long descriptions
        return trimmed.length > 80 ? trimmed.slice(0, 77) + '...' : trimmed;
      }
    }
  } catch {
    // Ignore read errors
  }

  return '';
}
