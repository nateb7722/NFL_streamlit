The purpose of this project is to create a streamlit app to view charts and see statistics to support NFL betting. We are currently working on version 1, which will have a page for team performance, a page for matchups (upcoming games), and a page to focus in on one specific team. 

Version 1 Instructions:

- The team performance page: 
  - This page should compare all teams, with a drop down to limit to a specific division or conference.
  - Chart of offensive epa by defensive epa. Defensive epa on x axis, offensive epa on y axis, and the x axis should be inverted to demonstrate that the lower the defensive epa, the better the team
  - offensive epa chart that has pass epa on the y axis and run epa on the x axis
  - defensive epa chart that has pass epa allowed on the y axis and run epa allowed on the x axis. Both axes should be inverted
  - strength of schedule chart that has average offensive epa of opponents on the y axis and average defensive epa of opponents on the x axis. X-axis should be inverted
- The matchups page:
  - This page should have a drop down for the upcoming matchup, or a drop down for home team and away team
  - It should show their overall records, record against the spread, and over under record
  - it should show average run yards and pass yards per game for each team
  - it should show average points scored and points allowed per game for each team
  - it should show average offensive epa and defensive epa for each team
  - it should show average offensive epa and defensive epa of their past opponents
  - it should show their record as a favorite and record as an underdog
  - it should show their record at home and record on the road
  - it should have a chart that shows weekly performance with overall team epa on the y axis and week number on the x axis for both teams
  - it should compare the ratings and stats for the weekly starters in the following categories:
    - pass blocking
    - run blocking
    - QB passing grades
    - QB running grades
    - receiving grades (includes WR and TE)
    - RB rushing grades
    - Run defense grades
    - Pass defense grades
    - Overall defensive grades
    - Special teams grades
    - pass rush grades
    - coverage grades
- The team specific page:
  - This page should have a drop down to select the team
  - It should show overall record, record against the spread, and over under record
  - it should show  run yards and pass yards per game
  - it should show  points scored and points allowed per game
  - it should show offensive epa and defensive epa per game
  - it should show record as a favorite and record as an underdog
  - it should show record at home and record on the road
  - it should have a chart that shows weekly performance with overall team epa on the y axis and week number on the x axis
  - it should show the difference in grades and stats between the healthy starters and weekly starters for each game for the following categories:
    - pass blocking
    - run blocking
    - QB passing grades
    - QB running grades
    - receiving grades (includes WR and TE)
    - RB rushing grades
    - Run defense grades
    - Pass defense grades
    - Overall defensive grades
    - Special teams grades
    - pass rush grades
    - coverage grades


Important Notes:
 - Documentation for the project should be created in a README.md file in the root of the project
 - Documentation on the available datasets created in the data pipelines can be found in the documentation folder inside the prod folder inside the nateb-nfl-project s3 bucket. The required parameters to download those files can be used by running the secrets.py file, which will create the environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_S3_BUCKET, and ENVIRONMENT (in this case it is 'Prod')
 - Charts should use the team's logo, which can be found in the aux folder inside the prod folder in a file called Team Logos.xlsx
 - Version 1 should not use the datasets game_df_team_week_averages_3_week_sequence, and training_data_full_game