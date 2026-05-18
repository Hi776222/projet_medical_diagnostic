import httpx


async def get_medical_reference():

    async with httpx.AsyncClient() as client:

        response = await client.get(
            "http://localhost:9000/reference"
        )

        return response.json()