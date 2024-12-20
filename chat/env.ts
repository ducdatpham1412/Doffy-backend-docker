import dotenv from "dotenv";

const env: any = dotenv.config({
    path: `chat/env/.env.${process.env.ENVIRONMENT_TYPE}`,
}).parsed;

export default env;
