# price-checker

This simple Flask application is a price checking tool to check Costco.com for a sale on certain items, as Costco does not provide automatic notifications for when an item goes on sale. This scrapes the site daily and will email you through SES (AWS) if the item is on sale.

# env variables

ACCESS_KEY_ID  
SECRET_ACCESS_KEY  
AWS_REGION  
TO_EMAIL=Destination email  
FROM_EMAIL=Email that has been registered and approved through SES (AWS)  
