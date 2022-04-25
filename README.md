# HTTP-Server


SimpleServer -> this server run HTTP/1.0 Protocol so once it send out the responses it closes the connection.  
PersistentServer -> this server run both HTTP/1.1 and HTTP/1.0 protocols so once it send out the responses it waits for more request from the client and then eventually closes the connection.  
PipelineServer -> this server run both HTTP/1.1 and HTTP/1.0 protocols but can handle mulitiple request from the same client either on a new connection or on the same connection.  




## Steps to Run.  

First compile all the C files.  

> make all


   
Then run the server you want (PersistentServer, SimpleServer, PipelinedServer) with a port number and the path to where all the server files are located.

> ./{SERVER TYPE} {PORT} {PATH}



ServerHelper.c has a set of functions which extract data from request and uses Parser.c function to send response
Parser.c has a set of functions to compile a response using the data provided
