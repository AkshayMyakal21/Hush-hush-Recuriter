import aiohttp

class GithubAPIClient:

    def __init__(self, token):
        self.token = token
        self.session = None

    async def __aenter__(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        self.session = aiohttp.ClientSession(headers=headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def get_user(self, username):
        url = f"https://api.github.com/users/{username}"

        async with self.session.get(url) as response:

            if response.status in range(200, 300):
                return await response.json()

            print(await response.text())

            raise Exception(
                f"Request failed with status code {response.status}"
                )
    async def get_rate_limit(self):
        url = "https://api.github.com/rate_limit"

        async with self.session.get(url) as response:
            return await response.json()
            
    async def search_users(self, query, limit):
        url = "https://api.github.com/search/users"
        params = {"q": query, "per_page": limit}
        async with self.session.get(url, params=params) as response:
            if response.status in range(200, 300):
                return await response.json()
            else:
                raise Exception(f"Request failed with status code {response.status}")
            
    async def get_user_repos(self, username):
        url = f"https://api.github.com/users/{username}/repos"
        params = {"per_page": 10}
        async with self.session.get(url, params=params) as response:
            if response.status in range(200,300):
                return await response.json()
            else:
                raise Exception(f"Request failed with status code {response.status}")
    
    async def get_user_events(self, username):
        url = f"https://api.github.com/users/{username}/events/public"
        params = {"per_page": 100}
        async with self.session.get(url, params=params) as response:
            if response.status in range(200,300):
                return await response.json()
            else:
                raise Exception(f"Request failed with status code {response.status}")