# statusly
**statusly** is a command-line tool that lets you log your daily developer work, track GitHub activity, and summarize everything using OpenAI GPT-4.1 API.

## features

- log tasks under DOING, DONE, BLOCKER, and MISC
- generate status reports with AI summaries
- automatically fetch:
  - PRs you opened (under DOING)
  - PRs you reviewed (under DONE)
- custom date ranges
- easy-to-use CLI

## installation

```bash
git clone https://github.com/yourusername/statusly.git
cd statusly
pip install -r requirements.txt
```

## setup

```bash
OPENAI_API_KEY=your_openai_key
GITHUB_TOKEN=your_github_token
GITHUB_USERNAME=your_github_username
```

## usage: start logging

1. add a log
`python cli.py log add --doing "Fixed bug in API" --done "Reviewed PR #123" --blocker "Waiting on deployment"`

2. show a log
`python cli.py show --log-date 2025-06-18`

3. ai summary
`python cli.py ai-summary --start-date 2025-06-01 --end-date 2025-06-18`

this fetches all logs and GitHub activity between the dates, and summarizes your week.

## things to implement:

