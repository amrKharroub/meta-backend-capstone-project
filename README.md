# meta-backend-capstone_project

available APIs:

- http:127.0.0.1:8000/restaurant
  
  renders the restaurant main page

- http:127.0.0.1:8000/restaurant/menu
  
  returns the menu items in available in the restaurant

- http:127.0.0.1:8000/restaurant/menu/<int id>
  
  returns a menu item refered by the id in the url

- http:127.0.0.1:8000/restaurant/api-token-auth
  
  returns token the user can use for authentication

- http://127.0.0.1:8000/restaurant/booking/tables/
  
  needs authentication
  
  returns all the bookings

- http://127.0.0.1:8000/auth/users/
  
  GET : returns all users
  
  POST: creates a new user

- 
