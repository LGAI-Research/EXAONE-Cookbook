#!/bin/bash
set -e

echo "Adding AI research blogs to blogwatcher-cli"

# Check if blogwatcher-cli is available
if ! command -v blogwatcher-cli &> /dev/null; then
    echo "Error: blogwatcher-cli not found. Please install it first."
    exit 1
fi

# Initialize blogwatcher-cli if not already
if [ ! -d "$HOME/.blogwatcher-cli" ]; then
    echo "Initializing blogwatcher-cli..."
    blogwatcher-cli init
fi

# Define feeds
feeds=(
    "AI Research Blogs"
    "AI Research Blogs" "https://thegradient.pub/feed"
    "AI Research Blogs" "https://distill.pub/feed"
    "AI Research Blogs" "https://ai.google/research/blog/atom.xml"
    "AI Research Blogs" "https://research.fb.com/feed"
    "AI Research Blogs" "https://d4m.org/feed"
    "AI Industry News"
    "TechCrunch AI" "https://techcrunch.com/tag/ai/rss.xml"
    "VentureBeat AI" "https://venturebeat.com/tag/ai-ar-vr/feed.xml"
    "AI Conferences"
    "NeurIPS" "https://neurips.cc/feed"
    "ICML" "https://icml.cc/feed"
    # Note: CVPR feed URL needs verification
    # "CVPR" "https://cvpr.org/Conference-Events/CVPR2026/Conference-Information/rss/"
)

# Add feeds
i=0
while [ $i -lt ${#feeds[@]} ]; do
    name="${feeds[i]}"
    url="${feeds[i+1]}"
    
    echo "---"
    echo "Adding feed: $name"
    echo "URL: $url"
    
    # Check if feed already exists
    existing=$(blogwatcher-cli blogs | grep -i "$name")
    if [ -n "$existing" ]; then
        echo "Feed '$name' already exists. Skipping."
    else
        # Add feed
        blogwatcher-cli add "$name" "$url"
        echo "Feed '$name' added successfully."
    fi
    
    i=$((i+2))
done

echo "\nAll feeds processed."
blogwatcher-cli blogs