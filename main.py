from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

app = FastAPI()

# MongoDB connection
client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client.property_management
properties_collection = db.properties

# Pydantic model for Property
class Property(BaseModel):
    property_name: str
    address: str
    city: str
    state: str

# API to create a new property
@app.post("/create_new_property/", response_model=Property)
async def create_new_property(property: Property):
    property_data = property.dict()
    result = await properties_collection.insert_one(property_data)
    new_property = await properties_collection.find_one({"_id": result.inserted_id})
    return new_property

# API to fetch properties by city
@app.get("/fetch_property/", response_model=list[Property])
async def fetch_property_details(city: str):
    properties = []
    async for property in properties_collection.find({"city": city}):
        properties.append(property)
    if not properties:
        raise HTTPException(status_code=404, detail="Properties not found")
    return properties

# API to update property details
@app.put("/update_property/{property_id}", response_model=Property)
async def update_property_details(property_id: str, property: Property):
    await properties_collection.update_one(
        {"_id": ObjectId(property_id)},
        {"$set": property.dict(exclude_unset=True)}
    )
    updated_property = await properties_collection.find_one({"_id": ObjectId(property_id)})
    if updated_property is None:
        raise HTTPException(status_code=404, detail="Property not found")
    return updated_property

# API to find cities by state
@app.get("/find_cities_by_state/", response_model=list[str])
async def find_cities_by_state(state: str):
    cities = []
    async for property in properties_collection.find({"state": state}):
        if property['city'] not in cities:
            cities.append(property['city'])
    if not cities:
        raise HTTPException(status_code=404, detail="Cities not found for the state")
    return cities

# API to find similar properties by city
@app.get("/find_similar_properties/", response_model=list[Property])
async def find_similar_properties(property_id: str):
    # Retrieve the property information for the given property_id
    property_info = await properties_collection.find_one({"_id": ObjectId(property_id)})
    if not property_info:
        raise HTTPException(status_code=404, detail="Property not found")

    # Extract the city of the property
    city = property_info['city']

    # Find all properties in the same city (excluding the original property)
    similar_properties = []
    async for property in properties_collection.find({"city": city}):
        if str(property['_id']) != property_id:
            # Create a Property object from the retrieved property data
            similar_property_obj = Property(**property)
            similar_properties.append(similar_property_obj)

    return similar_properties

# Run the FastAPI server with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
