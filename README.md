# Host analyser on Heroku

Intresting posts on dtf

## Getting Started

1. Download or clone this repository
2. Register on [Heroku](https://www.heroku.com/)
3. Download and install [Heroku CLI](https://devcenter.heroku.com/articles/getting-started-with-python#set-up)
4. Download and install [git](https://git-scm.com/downloads)
5. Open terminal.
   1. Auth Heroku

      ```bash
      heroku login
      ```

   2. Create heroku application

      ```bash
      heroku create
      ```
      
   3. Set env with your dtf api token

      ```bash
      heroku config:set TOKEN=your_token_here
      ```
      
   4. Provision postgresql database

      ```bash
      heroku addons:create heroku-postgresql:hobby-dev
      ```

   5. Add, commit and push your code into branch `master` of the
      remote `heroku`.

      ```bash
      git push heroku master
      ```

6. Specify the amount of worker that will run your application

    ```bash
    heroku ps:scale worker=1
    heroku ps:scale web=1
    ```

7. Now everything should be working. You can check your logs with this command

    ```bash
    heroku logs --tail
    ```

8. You can open the URL where the script is deployed using the below
    command (if you are deploying web application)

    ```bash
    heroku open
    ```

9. From now on you can use usual git commands (push, add, commit, etc.)
    to update your app. Every time you `push heroku master` your
    app gets redeployed with updated source code

10. To stop your application scale down the amount of workers with like this

     ```bash
    heroku ps:scale worker=0
    ```

### Prerequisites

* [Heroku CLI](https://devcenter.heroku.com/articles/getting-started-with-python#set-up)
* [git](https://git-scm.com/downloads)

## Authors

* @michaelkrukov - https://michaelkrukov.ru/

## Acknowledgments

* [Official guide to deploy app](https://devcenter.heroku.com/articles/getting-started-with-python#introduction)
* [Official guide about worker](https://devcenter.heroku.com/articles/background-jobs-queueing)
* [Guided "Simple twitter-bot with Python, Tweepy and Heroku"](http://briancaffey.github.io/2016/04/05/twitter-bot-tutorial.html)
