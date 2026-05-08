# Export Facebook Data

How to export only the data needed by `facebook-network-scorer`.

> [!WARNING]
> A Facebook export contains private messages, names, reactions, timestamps and account metadata.
> Keep it local.
> This project is designed to process your export locally.
> **Never commit real export files to git.**

---

## Step-by-step

### 1. Open Facebook Settings

1. Open [facebook.com](https://www.facebook.com) and log in.
2. Navigate to:
   - **Settings & privacy**
   - **Settings**
   - **Accounts Center**
   - **Your information and permissions**
   - **Export your information**

### 2. Create export

1. Click **Create export**.
2. Select the **Facebook profile** you want to analyze.
3. Choose **Export to device** (not "Transfer to destination").

### 3. Select information categories

Choose **Select specific information** and pick only what the scorer needs.

#### Required

| Category                | Why                                      |
|-------------------------|------------------------------------------|
| Friends                 | Canonical friend list                    |
| Followers               | Follower vs friend distinction           |
| Messages                | DM signal (bidirectional scoring)        |
| Posts                   | Post activity context                    |
| Comments and reactions  | Comment + reaction signals               |
| Interactions            | Additional interaction metadata          |

#### Optional

| Category              | Why                                        |
|-----------------------|--------------------------------------------|
| Stories               | Additional activity signal                 |
| Notifications         | Engagement hints                           |
| Profile information   | Owner name auto-detection                  |

#### Do not select unless needed

These categories add bulk without improving scoring:

- Location
- Payments
- Marketplace
- Dating
- Ads
- Apps and websites off Facebook
- Data logs
- Groups
- Pages
- Live videos
- Shops

### 4. Configure export format

| Setting         | Value        | Reason                                    |
|-----------------|--------------|-------------------------------------------|
| Format          | **JSON**     | The scorer parses JSON, not HTML          |
| Media quality   | **Low**      | Minimizes download size                   |
| Date range      | **1 year**   | Recommended balance of signal vs size     |

- **All Time** is supported but may produce a very large export.
- 1 year typically captures enough recent signal for scoring.

### 5. Download and extract

1. Click **Create export** to submit.
2. Wait for Facebook to prepare the ZIP (this can take minutes to hours).
3. Go to **Available downloads** when notified.
4. Download the ZIP file.
5. Extract the ZIP to a local folder.

---

## Expected folder structure

The exact folder names can vary by language and account settings.

Common examples after extraction:

```
facebook-yourname/
  connections/
    friends/
      your_friends.json
    followers/
  your_facebook_activity/
    messages/
      inbox/
        someperson_1234567890/
          message_1.json
    posts/
    comments_and_reactions/
      comments.json
      likes_and_reactions.json
  personal_information/
    profile_information/
      profile_information.json
  logged_information/
    interactions/
```

---

## Run the scorer

After extracting the export, point the scorer at the root folder:

```bash
python -m fb_network_scorer /path/to/facebook-export --output ./scored_output
```

### Windows

```powershell
python -m fb_network_scorer "C:\Users\You\Downloads\facebook-yourname" --output ".\scored_output"
```

### macOS / Linux

```bash
python -m fb_network_scorer ~/Downloads/facebook-yourname --output ./scored_output
```

---

## Output files

The scorer produces these CSV files in the output directory:

| File                          | Contents                              |
|-------------------------------|---------------------------------------|
| `fb_friend_score.csv`         | All contacts (friends + non-friends)  |
| `current_friends_scored.csv`  | All current friends with scores       |
| `current_friends_keep.csv`    | Friends classified as **keep**        |
| `current_friends_review.csv`  | Friends classified as **review**      |
| `current_friends_stale.csv`   | Friends classified as **stale**       |
| `non_friend_contacts.csv`     | Pages, groups, non-friend contacts    |

---

## Privacy checklist

Do **not** commit or upload any of the following:

- Raw Facebook ZIP files
- Extracted Facebook export folders
- Message JSON files
- Real CSV outputs containing real names
- Screenshots of Facebook UI
- Names from real datasets

The `.gitignore` in this repository is configured to exclude these by default.

---

## Troubleshooting

### Script finds 0 friends

- Check that **Friends** category was selected during export.
- Check that the ZIP was fully extracted.
- Check that the path points to the **root** export folder (the one containing `connections/`).

### Messages are missing

- Check that **Messages** category was selected.
- Facebook may take longer to prepare message exports - check **Available downloads** again later.

### Names look broken (mojibake)

- Facebook exports encode Vietnamese text as double-encoded UTF-8.
- The parser attempts automatic `latin-1 -> UTF-8` normalization.
- This is a known Facebook issue, not a bug in the scorer.

### Output includes too many contacts

- This is expected in the full graph output (`fb_friend_score.csv`).
- Use `current_friends_scored.csv` for cleanup decisions on your actual friend list.
- Non-friend contacts (pages, strangers) are separated into `non_friend_contacts.csv`.

### Export is too large

- Use **1 year** date range instead of All Time.
- Use **Low** media quality.
- Avoid exporting photos/videos categories unless you need them.
- Deselect unnecessary categories listed in "Do not select unless needed" above.
