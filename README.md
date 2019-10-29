## spotipy control
spotipy control is an open source library for controlling spotify connect devices based on the [librespot](https://github.com/librespot-org/librespot) project.  
spotipy control is a very limited python port. The focus is to login with your normal credentials (username, password)
or with your devices (spotify connect) to get a token for to use the spotify web api.
No need for a redirect url.

### Current status:
Under developing: No working example

### Installation
1. You will need python3 at least
2. Clone this repo
3. Install requirements:
````pip install requirements.txt````

### Run
1. Run
````python3 spotify.py -u username -p password -i client_id```` to get token with normal credentials

2. Run 
````python3 spotify.py -n 'Spotipy' -i client_id```` to advertise a speaker 'Spotipy', with which you can connect over
your devices.



### Optional
The repo comes with precompiled `protobuf` implementations. To generate them yourself,
download and install [Google Protocol Buffer](https://developers.google.com/protocol-buffers/docs/pythontutorial)
and then run 

````protoc -I=$SRC_DIR --python_out=$DST_DIR $SRC_DIR/file.proto````
 
 for each proto file. The generated files should be stored in the `/protocol/impl` folder.