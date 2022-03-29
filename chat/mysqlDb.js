import mysql from "mysql2";
import env from "./env.js";

const connectionObject = {
    host: env.DATABASE_HOST,
    user: env.DATABASE_USER,
    password: env.DATABASE_PASSWORD,
    port: env.DATABASE_PORT,
    database: env.DATABASE_NAME,
};

console.log("connection object:\n", connectionObject);

const con = mysql.createConnection(connectionObject);

con.connect();

export const executiveQuery = (query) => {
    return new Promise((resolve, reject) => {
        con.query(query, (err, res) => {
            if (err) reject(err);
            resolve(res);
        });
    });
};
