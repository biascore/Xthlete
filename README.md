# Overview

XTHLETE is a match management system for sports tournaments.
It generates fair fixtures, schedules matches across multiple courts, prevents player conflicts, ensures rest periods, and provides match codes for result entry, for security reasons.

This project's architecture is completely API driven. Everything is fetched from, and configurable via a database.

This is a submission for SPRINTX Hackathon's XTHLETE problem statement – Smart Fixture, Scheduling and Match Management System.

# Demo Video

https://files.catbox.moe/mst6t9.mp4


https://github.com/user-attachments/assets/0dd23662-db50-439f-8f9b-0c55145f41b8



# Live Demo URL
https://xthlete-280949975136.asia-south1.run.app/

# Features

## 1. Player, Team and Club Module
Register players with automatically generated unique player IDs, assign them a club and the event they would like to join.
Milestone 1 fully complete.

## 2. Fixture Generation
Creates tournament brackets on demand. Milestone 2 fully complete.

### Core rules implemented:
- Avoids same-club matchups as far as possible.
- Automatically allocates byes for odd player counts.
- Winner automatically advances and gets assigned to the next round.

## 3. Match Scheduling Engine
Assigns matches to courts and time slots using the previously generated brackets. Milestone 3 fully complete.

### Core rules implemented:
- Auto advances byes without scheduling their matches.
- Courts and timeslots are automatically allocated.
- No overlapping matches per court. If there's a delay, the second match waits till the first is complete.
- Minimum rest time (e.g., 10 minutes) after every match.
- Multi-court, multi-event scheduling. If there's multiple brackets scheduling their matches at the same time, rounds of equal depth are equally prioritised. Every next round goes to the next day.

## 4. Match Code System for Umpires
Each match gets a unique, automatically generated match code stored in the database. 
The umpire must enter this code to submit the scores. 
Milestone 3 fully complete.

## 5. Results, Standings and Leaderboard
Dynamically updates the brackets as matches are won, with scores and next round names. A panel to see the schedule of all upcoming matches is also provided. This panel is live and updates every 30 seconds.

### Core features:
- Final standings page (Winner, Runner-Up, Semifinalists, Quarterfinalists).
- Auto updated winner flow, with next round fixtures, fixed as soon as the umpire decides the match.
- Live leaderboard dynamically updated from a database.
- Auto-adjusting schedule for delays.

# Tech Stack

## Frontend
- HTML
- Tailwind CSS
- JavaScript

## Backend
- Flask (Python)
- Database: SQLite

# API Endpoints
- `GET /api/health` - Health check
- `GET /api/stats` - Tournament stats
- `GET /api/players` - Get all players
- `POST /api/players` - Add a new player
- `GET /api/fixtures` - Get tournament bracket
- `GET /api/schedule` - Get today's schedule
- `POST /api/validate-code` - Validate match code
- `POST /api/update-score` - Update match score
- `POST /api/submit-result` - Submit final result
- `GET /api/match/<code>` - Get details for that match
- `GET /api/clubs` - Get all clubs
- `GET /api/courts` - Get all courts
- `DELETE /api/players/<player_id>` - Delete that player
- `DELETE /api/players/<player_id>/force` - Delete that player, along with every match they are associated with
- `DELETE /api/players/force` - Delete all players
- `POST /api/generate-fixtures` - Generate fixtures
- `DELETE /api/fixtures` - Reset all fixtures
- `DELETE /api/fixtures/<category>` - Delete fixtures of only that category
- `POST /api/schedule-matches` - Schedule every match, even in the future based on fixtures




# Installation instructions 

### 1. Install Python dependencies
`pip install -r requirements.txt`

### 2. Start Flask server
`python smartmatch-backend.py`

### 3. Run app
Open the browser, type in `http://localhost:8080`

## Live demo: https://xthlete-280949975136.asia-south1.run.app/
