# marketplace-update-sales

Python script to automatically record Marketplace.tf sales to a Google Sheets spreadsheet. (Developed by @clone_two on Discord)

<img width="1383" alt="Screenshot 2024-06-12 at 5 40 00 PM" src="https://github.com/idomanteu/marketplace-update-sales/assets/126209266/4594ef2c-c2a9-4fa6-8196-e65155a83f48">

Records & matches Marketplace.tf item sales from a CSV export (must be an item export). All columns except item, date purchased, and price paid are automatically filled. For unrecorded sales, all data is automatically entered. Column formatting is self explanatory. 

Sheet name = Master Spreadsheet

Main worksheet = TF2

Max's worksheet = MSH

Unfiltered worksheet = Unrecorded Sales

z = pd.read_csv('marketplace_sales_76561199183171982_items.csv')

replace steamid --> :STONKS:
