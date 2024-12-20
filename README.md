# Pitch Usage Streamlit App
### This app shows data from the 2024 MLB season on how pitchers changed their pitch usage by time through the opposing order.

Data included is pitch usage, velocity, movement, and average run value. It is meant for exploratory purposes and should generate more questions about certain pitchers. For example, J.P. Sears
threw his fastball 43.6% of the time first time through, but dropped its usage to 31% and 31.6% on the second and third time through. It also saw worse results first time through, with an average
run value of -0.02 compared to 0.0 and 0.1, respectively. Why does he throw his fastball so much early on, and is this a possible fix for him to meaningfully improve? Questions like that can be 
derived from the simple data on this app.

pitch_usage.ipynb contains my brainstorming code, which is very rough.
pitch_usage_app.py contains the code for the Streamlit app.

The three parquet files each hold a third of the pitch by pitch data from 2024, as due to file size it required being split up. Enjoy!
