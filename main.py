import requests
import json
import time
import os
from datetime import datetime

# Define the API URL
api_url = os.environ.get("EPIC_GAMES_API_URL")

# Define the Discord webhook URL
webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")

def get_free_games():
    response = requests.get(api_url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch the API, status code: {response.status_code}")
    
    data = response.json()
    current_games = []
    upcoming_games = []
    
    # Extract the free games
    for game in data['data']['Catalog']['searchStore']['elements']:
        game_title = game['title']
        game_url = f"https://store.epicgames.com/en-US/p/{game['productSlug']}"
        if game['promotions']:
            # Current promotions
            if game['promotions']['promotionalOffers']:
                for promotion in game['promotions']['promotionalOffers']:
                    if promotion['promotionalOffers']:
                        current_games.append((game_title, game_url))
                        break

            # Upcoming promotions
            if game['promotions']['upcomingPromotionalOffers']:
                for upcoming in game['promotions']['upcomingPromotionalOffers']:
                    if upcoming['promotionalOffers']:
                        start_date = upcoming['promotionalOffers'][0]['startDate']
                        start_date = datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%S.%fZ')
                        if start_date > datetime.now():
                            upcoming_games.append((game_title, game_url, start_date))
                        break
    
    return current_games[:3], upcoming_games

def send_webhook_message(message, game, url):
    data = {
        "content": message
    }

    data["embeds"] = [
        {
            "title" : game,
            "url" : url,
        }
    ]

    response = requests.post(webhook_url, data=json.dumps(data), headers={"Content-Type": "application/json"})
    if response.status_code == 204:
        print("Webhook sent successfully")
    else:
        print("Failed to send webhook")

def main():
    last_sent_games = []
    last_checked_upcoming_games = []

    while True:
        try:
            current_games, upcoming_games = get_free_games()
            
            # Check if there are new free games
            if current_games != last_sent_games:
                message = "New free game available on Epic Games:\n"
                url = ""
                game = ""
                for i, (game, url) in enumerate(current_games):
                    # message += f"{i + 1}. {game}\n"
                    game = game
                    url = url
                
                send_webhook_message(message, game, url)
                last_sent_games = current_games

            # Check for upcoming games and notify when they become available
            for game, url, start_date in upcoming_games:
                if game not in last_checked_upcoming_games and start_date.date() == datetime.now():
                    send_webhook_message(f"The game '{game}' is now available for free on the Epic Games Store!", game, url)
                    last_checked_upcoming_games.append(game)
        
        except Exception as e:
            print(f"An error occurred: {e}")
        
        print("Sleeping for an hour...")
        time.sleep(60)  # Check every hour

if __name__ == "__main__":
    print("Starting the Epic Games Store free games checker...")
    main()
