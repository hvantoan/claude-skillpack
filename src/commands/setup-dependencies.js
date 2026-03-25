const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const { SKILLS_DIR } = require('../utils');

/**
 * Install skills + run install.sh/install.ps1 for dependencies.
 * @param {string[]} args - CLI arguments
 */
module.exports = function setupDependencies(args) {
  // First, run install command
  const installCmd = require('./install-skills');
  installCmd(args);

  // Then run the appropriate install script
  const isWindows = process.platform === 'win32';
  const scriptName = isWindows ? 'install.ps1' : 'install.sh';
  const scriptPath = path.join(SKILLS_DIR, scriptName);

  if (!fs.existsSync(scriptPath)) {
    console.log(`\nNo ${scriptName} found at ${scriptPath}. Skipping dependency installation.`);
    return;
  }

  console.log(`\nRunning ${scriptName} to install dependencies...\n`);

  try {
    const cmd = isWindows
      ? `powershell -ExecutionPolicy Bypass -File "${scriptPath}"`
      : `bash "${scriptPath}" -y`;

    execSync(cmd, {
      cwd: SKILLS_DIR,
      stdio: 'inherit',
      env: { ...process.env, NON_INTERACTIVE: '1' },
    });

    console.log('\nDependency installation complete!');
  } catch (err) {
    console.error(`\nDependency installation failed: ${err.message}`);
    console.log('You can run it manually:');
    console.log(`  cd ${SKILLS_DIR} && ./${scriptName}`);
    process.exit(1);
  }
};
