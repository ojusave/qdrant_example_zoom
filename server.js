const { fetchAllData } = require('./zoomapi');
const { exec } = require('child_process');
const path = require('path');
const readline = require('readline');
const { spawn } = require('child_process');

async function runPythonScript(scriptPath) {
    return new Promise((resolve, reject) => {
        const process = spawn('python3', [scriptPath]);

        process.stdout.on('data', (data) => {
            console.log(`Python stdout: ${data}`);
        });

        process.stderr.on('data', (data) => {
            console.error(`Python stderr: ${data}`);
        });

        process.on('close', (code) => {
            if (code === 0) {
                resolve();
            } else {
                reject(new Error(`Python script exited with code ${code}`));
            }
        });
    });
}

async function main() {
    try {
        await fetchAllData();
        console.log('All data fetched, now triggering Qdrant insertion.');

        const pythonInsertScriptPath = path.join(__dirname, 'vector', 'insert.py');
        await runPythonScript(pythonInsertScriptPath);
        console.log('Data inserted into Qdrant.');

        const rl = readline.createInterface({
            input: process.stdin,
            output: process.stdout
        });

        console.log('\nEnter your queries or type "exit" to quit.');

        const askQuery = () => {
            rl.question('Query: ', async (query) => {
                if (query.toLowerCase() === 'exit') {
                    rl.close();
                    process.exit(0);
                } else {
                    const pythonQueryScriptPath = path.join(__dirname, 'vector', 'query.py');
                    try {
                        const queryProcess = spawn('python3', [pythonQueryScriptPath, query]);
                        
                        queryProcess.stdout.on('data', (data) => {
                            console.log(`${data}`);
                        });

                        queryProcess.stderr.on('data', (data) => {
                            console.error(`Query error: ${data}`);
                        });

                        queryProcess.on('close', (code) => {
                            if (code !== 0) {
                                console.error(`Query process exited with code ${code}`);
                            }
                            askQuery();  // Ask for the next query
                        });
                    } catch (error) {
                        console.error('Error executing query:', error);
                        askQuery();  // Ask for the next query even if there was an error
                    }
                }
            });
        };

        askQuery();  // Start the query loop

    } catch (error) {
        console.error('Error in main process:', error);
        process.exit(1);
    }
}

main();