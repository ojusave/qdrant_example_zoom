const { makeApiCall } = require('./utils/apiutils');
const { getDateRange } = require('./utils/dateutils');
const { downloadVttFile, writeDataToFile } = require('./utils/fileutils');
const axios = require('axios');


function cleanUserData(user) {
    return {
        userid: user.id,
        firstname: user.first_name,
        lastname: user.last_name,
        email: user.email
    };
}

async function fetchMeetingSummary(meetingId) {
    try {
        const response = await makeApiCall(`/meetings/${meetingId}/meeting_summary`);
        console.log(`Fetched meeting summary for meeting ${meetingId}`);
        return response;
    } catch (error) {
        console.error(`Error fetching meeting summary for meeting ${meetingId}:`, error.message);
        return null;
    }
}

async function processRecording(recording) {
    let vttContent = null;
    for (const file of recording.recording_files) {
        if (file.file_type === 'TRANSCRIPT' && file.file_extension === 'VTT') {
            console.log(`Attempting to download VTT file for recording ${recording.uuid}`);
            console.log(`Download URL: ${file.download_url}`);
            try {
                // Special handling for VTT file download
                const response = await axios({
                    method: 'GET',
                    url: file.download_url,
                    headers: {
                        'Authorization': 'Bearer abc'
                    },
                    responseType: 'text'
                });
                vttContent = response.data;
                console.log(`Download completed for recording ${recording.uuid}`);
                
                if (vttContent === null) {
                    console.log(`VTT content is null for recording ${recording.uuid}`);
                } else if (vttContent === '') {
                    console.log(`VTT content is an empty string for recording ${recording.uuid}`);
                } else {
                    console.log(`VTT content received for recording ${recording.uuid}`);
                    console.log(`Content type: ${typeof vttContent}`);
                    console.log(`Content length: ${vttContent.length} characters`);
                    
                    const lines = vttContent.split('\n');
                    const totalLines = lines.length;
                    const previewLines = lines.slice(0, 10).join('\n'); // First 10 lines
                    console.log(`Total lines: ${totalLines}`);
                    console.log(`Preview (first 10 lines or less):\n${previewLines}`);
                    
                    if (totalLines <= 10) {
                        console.log('Entire VTT content shown above');
                    } else {
                        console.log('...');
                    }
                }
            } catch (error) {
                console.error(`Error downloading VTT file for recording ${recording.uuid}:`, error.message);
                if (error.response) {
                    console.error(`Response status: ${error.response.status}`);
                    console.error(`Response headers:`, error.response.headers);
                    console.error(`Response data:`, error.response.data);
                }
            }
            break;
        }
    }

    const meetingSummary = await fetchMeetingSummary(recording.uuid);

    return {
        uuid: recording.uuid,
        topic: recording.topic,
        start_time: recording.start_time,
        duration: recording.duration,
        vtt_content: vttContent,
        summary: meetingSummary ? {
            summary_title: meetingSummary.summary_title,
            summary_overview: meetingSummary.summary_overview,
            summary_details: meetingSummary.summary_details,
            next_steps: meetingSummary.next_steps
        } : null
    };
}
async function fetchUserRecordings(userId) {
    console.log(`Fetching recordings for user ${userId}`);
    const recordings = [];

    const dateRanges = getDateRange(6);

    for (const dateRange of dateRanges) {
        try {
            const response = await makeApiCall(`/users/${userId}/recordings`, {
                from: dateRange.from,
                to: dateRange.to,
                page_size: 300
            });
            console.log(`Fetched recordings for user ${userId} from ${dateRange.from} to ${dateRange.to}`);

            if (response && Array.isArray(response.meetings)) {
                for (const meeting of response.meetings) {
                    const processedRecording = await processRecording(meeting);
                    recordings.push(processedRecording);
                }
            } else {
                console.log(`No recordings found for user ${userId} in date range ${dateRange.from} to ${dateRange.to}`);
            }
        } catch (error) {
            console.error(`Error fetching recordings for user ${userId}:`, error.message);
        }
    }

    return recordings;
}

async function fetchAllData() {
    try {
        const response = await makeApiCall('/users');
        console.log('Users API response:', JSON.stringify(response, null, 2));

        let users = [];
        if (response && response.users && Array.isArray(response.users)) {
            users = response.users;
        } else if (response && typeof response === 'object') {
            users = [response];
        }

        if (users.length === 0) {
            console.log('No users found in the API response');
            return;
        }

        // Limit to the first 5 users
        const usersToProcess = users.slice(0, 5);
        console.log(`Processing the first ${usersToProcess.length} users`);

        for (const user of usersToProcess) {
            const cleanedUser = cleanUserData(user);
            const recordings = await fetchUserRecordings(user.id);

            const userData = {
                ...cleanedUser,
                recordings: recordings
            };

            // Save the data to a file (to be used by the Python script)
            await writeDataToFile(userData, `user_${user.id}`);
            console.log(`Processed ${recordings.length} recordings for user ${user.id}`);
        }

        console.log('All data fetched and saved successfully for the first 5 users');
    } catch (error) {
        console.error('Error in fetchAllData:', error);
    }
}

module.exports = { fetchAllData };
