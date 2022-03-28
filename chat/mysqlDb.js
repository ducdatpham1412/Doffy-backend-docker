import mysql from "mysql2";
import env from "./env.js";

const con = mysql.createConnection({
    host: env.DATABASE_HOST,
    user: env.DATABASE_USER,
    password: env.DATABASE_PASSWORD,
    port: env.DATABASE_PORT,
    database: env.DATABASE_NAME,
});

con.connect();

export const executiveQuery = (query) => {
    return new Promise((resolve, reject) => {
        con.query(query, (err, res) => {
            if (err) reject(err);
            resolve(res);
        });
    });
};
