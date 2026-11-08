# CHANGELOG

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
