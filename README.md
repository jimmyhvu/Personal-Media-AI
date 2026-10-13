# Personal Media AI

A personal media discovery and recommendation application built with Python, Streamlit, and the OpenAI API.

The application combines user reviews, media preferences, and external data sources to provide personalized recommendations across games, movies, television, music, and books.

## Features

- **Discover:** AI-generated recommendations based on personal tastes, with optional web search for current information.
- **Evaluate:** Assess specific media against an evolving preference profile.
- **Watchlist:** Save and manage media of interest, including artwork and availability information.
- **Add Review:** Record ratings and reactions, with AI-assisted suggestions for building a review history.
- **Media Chat:** Discuss media with an LLM and optionally preserve useful insights as reference notes or reactions.
- **Data integrations:** Incorporate Steam and Spotify listening/play history into a cross-media preference profile.

## Technology

- Python
- Streamlit
- OpenAI API
- TMDB API
- Local JSON/JSONL data storage

## Running locally

1. Clone the repository.
2. Install dependencies using `pip install -r requirements.txt`.
3. Create a `.env` file based on `.env.example`.
4. Add your own API credentials.
5. Run `streamlit run media_app.py`.

The application requires an OpenAI API key for AI-powered functionality. Some features also require TMDB credentials.

This repository contains application source code, not the author's personal media history or API credentials. Some features depend on locally generated preference data and may require additional initialization.

## Development

This project was developed through an iterative, AI-assisted workflow using ChatGPT. I directed feature design, integration decisions, testing, and refinement while using AI to accelerate Python development.

The project explores how modern AI development tools can enable someone with a technical product and implementation background to build customized software for practical use.
