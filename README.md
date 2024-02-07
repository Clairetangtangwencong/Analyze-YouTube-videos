# YouTube-api
### Purpose statement 
The objective of this project is to
1) Extract information about all videos of one channel, including Likes, Views, Comments
2) Analyze performance of the channel and its videos
The project is divided intoo two parts: 1) Extract video information; 2) Analyse performance

### Steps in Extract video information.ipynb
1. Import libraries
2. Set Up
2.1. enable your YouTube API https://developers.google.com/youtube/v3
2.2. download your credentials from
https://console.developers.google.com/apis/credentials and save as credentials.json
2.3. Authenticate to YouTube API
3. Get Video Information
3.1. Parse Channel URL to get Channel ID
3.2. Get video URLs from Channel
3.3. Get video details from URLs
3.4. Print video infos
4. Store Video Information

