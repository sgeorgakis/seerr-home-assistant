### Features

- [ ] create functionality to fetch all pending requests. use the `GET /requests?take={pageSize}&skip={pageNumber}&filter=pending&sort=added&sortDirection=desc` endpoint
      I have passed configurable query parameters and constants. make configurable only the ones I have explicitly made so.
      Example request:
```
   {
  "pageInfo": {
    "page": 1,
    "pages": 10,
    "results": 100
  },
  "results": [
    {
      "id": 123,
      "status": 0,
      "media": "string",
      "createdAt": "2020-09-12T10:00:27.000Z",
      "updatedAt": "2020-09-12T10:00:27.000Z",
      "requestedBy": {
        "id": 1,
        "email": "hey@itsme.com",
        "username": "string",
        "plexUsername": "string",
        "plexToken": "string",
        "jellyfinAuthToken": "string",
        "userType": 1,
        "permissions": 0,
        "avatar": "string",
        "createdAt": "2020-09-02T05:02:23.000Z",
        "updatedAt": "2020-09-02T05:02:23.000Z",
        "requestCount": 5
      },
      "modifiedBy": {
        "id": 1,
        "email": "hey@itsme.com",
        "username": "string",
        "plexUsername": "string",
        "plexToken": "string",
        "jellyfinAuthToken": "string",
        "userType": 1,
        "permissions": 0,
        "avatar": "string",
        "createdAt": "2020-09-02T05:02:23.000Z",
        "updatedAt": "2020-09-02T05:02:23.000Z",
        "requestCount": 5
      },
      "is4k": false,
      "serverId": 0,
      "profileId": 0,
      "rootFolder": "string"
    }
  ]
  }
```
- [ ] create functionality to fetch a single request from its id. use the `GET /request/{requestId}` endpoint.
      Example response: 
      ```
      {
  "id": 123,
  "status": 0,
  "media": "string",
  "createdAt": "2020-09-12T10:00:27.000Z",
  "updatedAt": "2020-09-12T10:00:27.000Z",
  "requestedBy": {
    "id": 1,
    "email": "hey@itsme.com",
    "username": "string",
    "plexUsername": "string",
    "plexToken": "string",
    "jellyfinAuthToken": "string",
    "userType": 1,
    "permissions": 0,
    "avatar": "string",
    "createdAt": "2020-09-02T05:02:23.000Z",
    "updatedAt": "2020-09-02T05:02:23.000Z",
    "requestCount": 5
  },
  "modifiedBy": {
    "id": 1,
    "email": "hey@itsme.com",
    "username": "string",
    "plexUsername": "string",
    "plexToken": "string",
    "jellyfinAuthToken": "string",
    "userType": 1,
    "permissions": 0,
    "avatar": "string",
    "createdAt": "2020-09-02T05:02:23.000Z",
    "updatedAt": "2020-09-02T05:02:23.000Z",
    "requestCount": 5
  },
  "is4k": false,
  "serverId": 0,
  "profileId": 0,
  "rootFolder": "string"
}
      ```
- [ ] create functionality to update a request. use the `POST /request/{requestId}/{status}` endpoint, where status can be either approve or decline
      Example response:    
  ```
      {
  "id": 123,
  "status": 0,
  "media": "string",
  "createdAt": "2020-09-12T10:00:27.000Z",
  "updatedAt": "2020-09-12T10:00:27.000Z",
  "requestedBy": {
    "id": 1,
    "email": "hey@itsme.com",
    "username": "string",
    "plexUsername": "string",
    "plexToken": "string",
    "jellyfinAuthToken": "string",
    "userType": 1,
    "permissions": 0,
    "avatar": "string",
    "createdAt": "2020-09-02T05:02:23.000Z",
    "updatedAt": "2020-09-02T05:02:23.000Z",
    "requestCount": 5
  },
  "modifiedBy": {
    "id": 1,
    "email": "hey@itsme.com",
    "username": "string",
    "plexUsername": "string",
    "plexToken": "string",
    "jellyfinAuthToken": "string",
    "userType": 1,
    "permissions": 0,
    "avatar": "string",
    "createdAt": "2020-09-02T05:02:23.000Z",
    "updatedAt": "2020-09-02T05:02:23.000Z",
    "requestCount": 5
  },
  "is4k": false,
  "serverId": 0,
  "profileId": 0,
  "rootFolder": "string"
   }
  ```
- [ ] create functionality to create a new request. use the `POST /request/` endpoint
      Example request body:
    ```
   {
  "mediaType": "movie",
  "mediaId": 123,
  "tvdbId": 123,
  "seasons": [
    0
  ],
  "is4k": false,
  "serverId": 0,
  "profileId": 0,
  "rootFolder": "string",
  "languageProfileId": 0,
  "userId": 0
  }
  ```
  
  Example Response: 
  ```{
  "id": 123,
  "status": 0,
  "media": "string",
  "createdAt": "2020-09-12T10:00:27.000Z",
  "updatedAt": "2020-09-12T10:00:27.000Z",
  "requestedBy": {
    "id": 1,
    "email": "hey@itsme.com",
    "username": "string",
    "plexUsername": "string",
    "plexToken": "string",
    "jellyfinAuthToken": "string",
    "userType": 1,
    "permissions": 0,
    "avatar": "string",
    "createdAt": "2020-09-02T05:02:23.000Z",
    "updatedAt": "2020-09-02T05:02:23.000Z",
    "requestCount": 5
  },
  "modifiedBy": {
    "id": 1,
    "email": "hey@itsme.com",
    "username": "string",
    "plexUsername": "string",
    "plexToken": "string",
    "jellyfinAuthToken": "string",
    "userType": 1,
    "permissions": 0,
    "avatar": "string",
    "createdAt": "2020-09-02T05:02:23.000Z",
    "updatedAt": "2020-09-02T05:02:23.000Z",
    "requestCount": 5
  },
  "is4k": false,
  "serverId": 0,
  "profileId": 0,
  "rootFolder": "string"
  }
  ```