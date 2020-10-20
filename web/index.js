const express = require ('express');
const mysql = require('mysql');
const app = express();

app.use( express.static( "public" ) );

//------------------------------------------------------------------------------
//establish SQL connection.
var env = process.env.NODE_ENV || 'development';
console.log("connecting to MySQL with " + env + " credentials...");
var config = require('./config')[env];

let con = mysql.createPool(config.database);

//------------------------------------------------------------------------------

app.get('/',(req, res) => {
  let query = "SELECT * FROM `search_terms` ORDER BY id ASC";

  // execute query
  con.query(query, (err, result) => {
      if (err) {
          res.redirect('/');
          return;
      }
      res.render('index.ejs', {searchterms: result});
      return;
  });
});

app.get('/searchterm/:id', (req, res) => {
  let id = parseInt(req.params.id)
  let searchInformation;
  let query = "SELECT * FROM search_terms WHERE id=" + id + " LIMIT 1;";

  //check if the ID is valid to prevent SQL injection attack.
  if (isNaN(id)){
    res.sendStatus(403);
    return;
  }
  else{
    // get the details of the search term from the database.
    con.query(query, (err, result) => {
        if (err) {
          console.log("there was an issue with querying the database for a term.")
          console.log(err.message)
          res.redirect('/');
          return;
        }
        searchInformation = result;

        query = "SELECT * FROM expired_listings WHERE search_id="+ id + " ORDER BY close_datetime DESC LIMIT 10;";

        // get the expired listings under the search term to display in the table.
        con.query(query, (err, result) => {
            if (err) {
              console.log("there was an issue with querying the database for a term.")
              console.log(err.message)
              res.redirect('/');
              return;
            }
            res.render('term_view.ejs', {recentListings: result, search_id: id, search_information: searchInformation[0]});
            return;
        });
    });
  }
});

//Get JSON of recently expired listings for a specific search.
app.get('/searchterm/:id/expiredlistings', (req, res) => {
  let id = parseInt(req.params.id);
  let query = "SELECT * FROM TradeMe_Tracker.expired_listings WHERE search_id="+ id + " ORDER BY close_datetime DESC LIMIT 10;"

  //check if the ID is valid to prevent SQL injection attack.
  if (isNaN(id)){
    res.sendStatus(403);
    return;
  }
  else{
    // execute query
    con.query(query, (err, result) => {
        if (err) {
          console.log("there was an issue with querying the database for a term.")
          console.log(err.message)
          res.redirect('/');
          return;
        }
        res.send(result)
        return;
    });
  }
});

//Get JSON of long term data for a specific search.
app.get('/searchterm/:id/longtermdata.json', (req, res) => {
  let id = parseInt(req.params.id);
  let query = "SELECT * FROM `long_term_data` WHERE search_id = "+ id + " ORDER BY date ASC;"

  //check if the ID is valid to prevent SQL injection attack.
  if (isNaN(id)){
    res.sendStatus(403);
    return;
  }
  else{
    // execute query
    con.query(query, (err, result) => {
        if (err) {
          console.log("there was an issue with querying the database for a term.")
          console.log(err.message)
          res.redirect('/');
          return;
        }
        res.send(result)
        return;
    });
  }
});

//------------------------------------------------------------------------------

app.listen(3000, () => console.log('listening on port 3001'))
