

# deployment inEC2 instance
## pm2 is a production-grade process manager for Node.js applications that ensures your app runs even after you close the terminal. It also provides additional features like auto-restart on failure or system reboots.

1.sudo npm install -g pm2
2.pm2 start npm --name "verba-app" -- run start
3.pm2 list

## Keep pm2 Running After System Reboots (Optional): To ensure pm2 starts your app automatically after the EC2 instance reboots:
4.pm2 startup
5.pm2 save


## To view your app's logs, use the following command:

6.pm2 logs verba-app
7.pm2 stop verba-app


pm2 restart verba-app

##Ensure Environment Variables are Set (if applicable)
If your app depends on environment variables, make sure they are properly set when running with PM2. You can pass environment variables to PM2 like this:

pm2 start npm --name "verba-app" -- start --env production




