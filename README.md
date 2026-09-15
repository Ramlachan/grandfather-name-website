# Grandfather Name Website

A small Flask + SQLite web application where each browser can submit one grandfather's name, while the owner can privately view submissions.

## Requirements

- Python 3.11+ recommended
- Windows, macOS, or Linux
- A browser

## Windows setup

Open PowerShell or Command Prompt inside this project folder.

### 1. Create a virtual environment

PowerShell:

```powershell
py -m venv .venv
```

If `py` does not work, try:

```powershell
python -m venv .venv
```

### 2. Activate it

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Command Prompt:

```cmd
.venv\Scripts\activate
```

### 3. Install Flask

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Set the owner password

PowerShell (only for the current terminal window):

```powershell
$env:OWNER_PASSWORD="ReplaceThisWithYourStrongPassword"
```

Also set a Flask session secret for this terminal:

```powershell
$env:FLASK_SECRET_KEY="ReplaceThisWithARandomLongSecret"
```

Command Prompt:

```cmd
set OWNER_PASSWORD=ReplaceThisWithYourStrongPassword
set FLASK_SECRET_KEY=ReplaceThisWithARandomLongSecret
```

Do not put either secret in `app.py` or commit them to source control.

### 5. Start the server

```powershell
python app.py
```

You should see Flask listening on:

`http://127.0.0.1:5000`

### 6. Open the public website

Visit:

`http://127.0.0.1:5000/`

### 7. Open the owner dashboard

Visit:

`http://127.0.0.1:5000/owner/login`

Enter the password you set in `OWNER_PASSWORD`.

## Testing

1. Open the public page.
2. Enter a grandfather's name.
3. Click **Share name**.
4. Confirm that a success page appears.
5. Try submitting again from the same browser. It should be rejected.
6. Open `/owner/login` and sign in.
7. The dashboard should show the submission and total count.
8. Click **Log out**.
9. Confirm that `/owner` redirects to the login page.

## Database

The first startup automatically creates:

`submissions.db`

It contains:

- `id`: unique submission ID
- `grandfather_name`: submitted name
- `submitted_at`: UTC timestamp
- `browser_token_hash`: hashed long-lived browser token used for duplicate protection

Do not place `submissions.db` in a public web directory or upload it to a public repository.

## Important limitation of one-device protection

The first version uses a long-lived, HttpOnly browser cookie. It is intentionally not an IP-address rule.

It normally prevents the same browser from submitting twice, but it is not a perfect physical-device identity system. A person can clear cookies, use another browser/profile, use private browsing, or use another device.

If stronger enforcement is needed later, the application can add a stronger identity layer such as verified accounts, email/phone verification, or another trusted verification mechanism.

## Local-only vs public deployment

This project is configured for local Windows development.

If you later publish it on the internet, use HTTPS and a production WSGI server. At that point, change the submission cookie's `secure` setting to `True`, keep secrets outside the source code, and use a stronger deployment architecture. SQLite is fine for a small first version but may eventually be replaced by a server database if traffic grows.
