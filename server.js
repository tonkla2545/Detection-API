const express = require('express')
const cors = require('cors')
const {readdirSync } = require('fs')
const path = require('path')
require("dotenv").config();


const app = express()
app.use(cors())

app.use('/uploads', express.static(path.join(__dirname, 'uploads')));
app.use('/runs', express.static(path.join(__dirname, 'runs')));

readdirSync('./routes').map((item)=> 
    app.use('/api',require('./routes/'+item))) // map is loop

app.listen(5002, () => {
    console.log('Server is running on http://localhost:5002')
})