// Generated by CoffeeScript 1.8.0
(function() {
  var MongoClient, collection, index, query;

  MongoClient = require('mongodb').MongoClient;

  collection = null;

  MongoClient.connect("mongodb://localhost:27017/sybbs", function(error, db) {
    if (error) {
      console.dir(error);
      return process.exit(1);
    } else {
      return collection = db.collection('thread');
    }
  });

  index = function(request, response) {
    response.writeHead(200, {
      'Content-Type': 'text/html;charset=UTF-8'
    });
    response.write('Hello index');
    return response.end();
  };

  query = function(request, response) {
    var execQuery, postData;
    if (request.method !== 'POST') {
      response.writeHead(403, {
        'Content-Type': 'text/html;charset=UTF-8'
      });
      response.write('POST!');
      response.end();
    } else {
      postData = '';
      request.setEncoding('utf8');
      request.addListener('data', function(chunk) {
        return postData += chunk;
      });
      request.addListener('end', function() {
        var exception;
        try {
          return execQuery(JSON.parse(postData).join('|'), response);
        } catch (_error) {
          exception = _error;
          response.writeHead(403, {
            'Content-Type': 'text/html;charset=UTF-8'
          });
          response.write('invalid post data');
          return response.end();
        }
      });
    }
    return execQuery = function(regexString, response) {
      return collection.find({
        $or: [
          {
            title: {
              $regex: regexString
            }
          }, {
            reply: {
              $regex: regexString
            }
          }
        ]
      }).toArray(function(error, result) {
        if (error) {
          response.writeHead(500, {
            'Content-Type': 'text/html;charset=UTF-8'
          });
          response.write(error);
          return response.end();
        } else {
          response.writeHead(200, {
            'Content-Type': 'application/json;charset=UTF-8'
          });
          response.write(JSON.stringify(result));
          return response.end();
        }
      });
    };
  };

  exports.index = index;

  exports.query = query;

}).call(this);
