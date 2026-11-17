# CHANGELOG

## 17.11.2026 - 6/Homework 4 (Part 1: users and JWT)
### Added
- Added Django REST Framework and Simple JWT, all API URLs have no / at the end
- Added the auths API at /api/auths/v1/: register, login, token refresh and the user's own profile (users/me)
- Register checks the password with AUTH_PASSWORD_VALIDATORS, saves the email in lower case and hashes the password with create_user()
- Login works with the email in any case, a wrong email, a wrong password or an inactive user all get the same "Invalid email or password." answer
- Login puts the tokens into the X-Access-Token and X-Refresh-Token response headers, token refresh puts the new access token into X-Access-Token
- users/me shows the profile, PATCH changes only first_name and last_name
- Added ValidationMixin in apps/common/mixins.py, "check the data or answer 400" is written once for all ViewSets
- Access token lives 15 minutes, refresh token 1 day

### Changed
- The default permission is IsAuthenticated, public endpoints (register, login, token refresh) set their own
- Added djangorestframework-simplejwt, redis and celery[redis] to requirements

## 16.11.2026 - 5/Homework 3
### Added
- Added 50 ORM queries in apps/blog/queries.py
- Added the queries command with --number and --sql, it shows the result and the number of SQL queries
- Updated the readme with the queries command

### Changed
- Seed makes realistic dates for posts and comments

## 09.11.2026 - 4/Homework 2
### Added
- Added the seed command that fills the db with fake users, categories, tags, posts and comments
- Seed has --users, --posts, --comments and --clear options and prints a summary at the end
- Added Django Unfold to the admin panel
- Changed the admin title and colors to pink, added the Local/Production badge and links to github and unfold docs
- Added the sidebar menu with a drafts counter on Posts, Users & Access is shown only for superusers
- Added All / Published / Drafts tabs on the posts page
- Added the dashboard with cards, a chart of posts per category, top 5 authors and published/draft progress bars
- Posts admin: status labels, tags dropdown, filters, comments when you open a row, tabs on the edit page and a text editor
- Added actions for posts: publish / move to drafts, publish all drafts, open comments, save & publish
- Users admin: initials and email in one column, active/staff labels, tabs on the edit page, activate/deactivate users
- Comments, categories and tags admin: search, filters, post counts
- Updated the readme with how to run the project, the seed command and admin screenshots

### Changed
- Pinned django and added django-unfold and faker to requirements
- SQL logging in local settings is off by default, can be turned on to check queries

### Fixed
- Tabs on the user edit page were not showing because of old hw1 code left in the admin
- Seed now always makes at least one inactive and one staff user
- Removed the db backup file from git

## 05.10.2026 - 3/Project upload
### Added
- Added the project according to the hw1
- Added the docs/erd file that shows the project structure

### Fixed
- Migrations updated

## 04.10.2026 - 2/Project Structure setup
### Added
- Added the project files according to the hw1 requirement structure
### Changed
- Updated the gitignore to keep .env only locally

## 04.10.2026 - 1/Initial Commit 
### Added
- Added a Changelog
- Added a Readme
