import { MongoClient } from "mongodb";

const uri = `mongodb://username:password@www.doffy.xyz:27017/?authSource=admin&readPreference=primary&serverSelectionTimeoutMS=5000&directConnection=true&ssl=false`;

const client = new MongoClient(uri);
client.connect();
const mongoDb = client.db("doffy");

const query = async () => {
    const listOldMessage = await (
        await mongoDb
            .collection("__old_message")
            .find({}, { session: client.startSession() })
    ).toArray();

    listOldMessage.forEach(async (message) => {
        const newMessage = {
            _id: message._id,
            type: message.type,
            content: message.content,
            creator: message.creator_id,
            created: message.created,
            conversation_id: message.channel_id,
            status: 1,
        };
        await mongoDb.collection("chat_message").insertOne(newMessage);
    });
};

query();
