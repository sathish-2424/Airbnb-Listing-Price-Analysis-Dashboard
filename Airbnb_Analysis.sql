SELECT *
FROM airbnb_listings
LIMIT 10;

-- Total Number of Listings
SELECT COUNT(*) AS total_listings
FROM airbnb_listings;

-- Average Price by Neighborhood
SELECT neighbourhood_group,
       AVG(price) AS avg_price
FROM airbnb_listings
GROUP BY neighbourhood_group
ORDER BY avg_price DESC;

-- Listings Count by Room Type
SELECT room_type,
       COUNT(*) AS total_listings
FROM airbnb_listings
GROUP BY room_type;

-- Top 10 Most Expensive Listings
SELECT neighbourhood,
       room_type,
       price
FROM airbnb_listings
ORDER BY price DESC
LIMIT 10;

-- Most Reviewed Listings
SELECT neighbourhood,
       price,
       number_of_reviews
FROM airbnb_listings
ORDER BY number_of_reviews DESC
LIMIT 10;

-- Average Price by Room Type
SELECT room_type,
       AVG(price) AS avg_price
FROM airbnb_listings
GROUP BY room_type
ORDER BY avg_price DESC;


-- Neighborhoods with Highest Listings
SELECT neighbourhood,
       COUNT(*) AS listing_count
FROM airbnb_listings
GROUP BY neighbourhood
ORDER BY listing_count DESC
LIMIT 10;

-- Availability Analysis
SELECT neighbourhood_group,
       AVG(availability_365) AS avg_availability
FROM airbnb_listings
GROUP BY neighbourhood_group
ORDER BY avg_availability DESC;

-- Price Distribution by Room Type
SELECT room_type,
       MIN(price) AS min_price,
       MAX(price) AS max_price,
       AVG(price) AS avg_price
FROM airbnb_listings
GROUP BY room_type;