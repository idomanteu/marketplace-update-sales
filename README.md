# marketplace-update-sales

Python script to automatically record Marketplace.tf sales to a Google Sheets spreadsheet. (Developed by @clone_two on Discord)

<img width="1383" alt="Screenshot 2024-06-12 at 5 40 00 PM" src="https://github.com/idomanteu/marketplace-update-sales/assets/126209266/4594ef2c-c2a9-4fa6-8196-e65155a83f48">

The primary function of this script is to record & match item sales. (Main script) All columns except item, date purchased, and price paid are automatically filled. For unrecorded sales, all data is automatically entered.

___

Required Python libraries:

`pip install gspread`
`pip install functools`
`pip install dotenv`

# Setup:
1) Generate Marketplace API Key at https://marketplace.tf/apisettings and replace `MPKEY` variable in .env file
2) Follow the instructions for registering a service account at https://docs.gspread.org/en/latest/oauth2.html#for-bots-using-service-account and copy the json file contents into `service_account.json`
3) Create a new spreadsheet titled `Master Spreadsheet` and 4 worksheets:  
  - `TF2` - Matches and records items in your main sheet
  - `MSH` - Matches and records sales for Max's Severed Heads (Optional, but you will need to make an empty sheet for it anyway)
  - `Unrecorded Sales` - Records all otherwise unrecorded sales
  - `IDs` - Used to write all sales IDs
4) Update the `LASTSEARCH` variable in the .env file with the first sale you'd like to record. The script will paginate through all sales & continue to refresh as long as it's running.

## Important info:
The naming scheme is based off Backpack.tf item names. If a sale isn't recorded, it's likely that the script wasn't able to find a match. If you record spells and other items that don't follow the same naming scheme, they will be skipped. You can check unrecorded sales to update any missing entries.

The worksheet names must match the variables in the update-sales python script.

  <img width="424" alt="Master Spreadsheet screenshot" src="https://github.com/idomanteu/marketplace-update-sales/assets/126209266/d8605a9c-d3f6-47f1-8db3-0da9208cf69a">
  
  <img width="359" alt="Worksheets screenshot" src="https://github.com/idomanteu/marketplace-update-sales/assets/126209266/1df4701d-bb08-4265-88b0-fdce1dc9afb4">

# Column names:
(so the entries actually make sense...)

TF2 worksheet column titles

`Type	Class	Quality	Item	Date Purchased	Paid (USD)	Date Sold	Sold (USD)	TTS (Days)	Profit (USD)	ROIC	ID`

<img width="1000" alt="Screenshot 2024-06-12 at 4 41 19 PM" src="https://github.com/idomanteu/marketplace-update-sales/assets/126209266/8f03dd15-ec88-45b8-9212-19a8c420a2c5">

If you want to record your prices in keys instead of USD you can simply add an additional column to divide the Marketplace.tf sale prices by the corresponding key rate.

___

MSH worksheet column titles

`Date Purchased	Paid (USD)	Date Sold	Sold (USD)	TTS (Days)	Profit (USD)	ROIC	ID`

<img width="1092" alt="Screenshot 2024-06-12 at 4 44 54 PM" src="https://github.com/idomanteu/marketplace-update-sales/assets/126209266/002776c4-d1b2-40fa-ac78-0c8402e47a7a">

___

Unrecorded Sales worksheet column titles

`Type	Class	Quality	Item	Date Sold	Price Sold (USD)	ID`

<img width="526" alt="Screenshot 2024-06-12 at 4 51 21 PM" src="https://github.com/idomanteu/marketplace-update-sales/assets/126209266/ca45356a-8be5-43e9-a9a7-09ef4ee03f77">

