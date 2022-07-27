import mysql from "mysql2";
import env from "./env";

const connectionObject: any = {
    host: env.DATABASE_HOST,
    user: env.DATABASE_USER,
    password: env.DATABASE_PASSWORD,
    port: env.DATABASE_PORT,
    database: env.DATABASE_NAME,
};

export const executiveQuery = (query: string): Promise<any> => {
    const con = mysql.createConnection(connectionObject);

    return new Promise((resolve, reject) => {
        con.connect((err) => {
            if (err) reject(err);
            con.query(query, (err, res) => {
                if (err) reject(err);
                con.end((err) => {
                    if (err) reject(err);
                    resolve(res);
                });
            });
        });
    });
};
