SELECT * FROM airbnb;

SELECT COUNT(*) AS total_listings
FROM airbnb;

SELECT AVG(price) AS avg_price
FROM airbnb;

-- Listings by Room Type
SELECT room_type, COUNT(*) AS total
FROM airbnb
GROUP BY room_type
ORDER BY total DESC;

-- Average Price by Room Type
SELECT room_type, AVG(price) AS avg_price
FROM airbnb
GROUP BY room_type
ORDER BY avg_price DESC;

-- Top 10 Most Expensive Listings
SELECT name, neighbourhood, price
FROM airbnb
ORDER BY price DESC
LIMIT 10;

-- Listings by Neighborhood
SELECT neighbourhood, COUNT(*) AS listings
FROM airbnb
GROUP BY neighbourhood
ORDER BY listings DESC;

-- Average Reviews by Room Type
SELECT room_type, AVG(number_of_reviews) AS avg_reviews
FROM airbnb
GROUP BY room_type;

-- Listings with High Availability
SELECT name, availability_365
FROM airbnb
WHERE availability_365 > 300;

-- Most Active Hosts
SELECT host_name, COUNT(*) AS total_listings
FROM airbnb
GROUP BY host_name
ORDER BY total_listings DESC
LIMIT 10;