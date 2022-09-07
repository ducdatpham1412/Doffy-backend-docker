import { MongoClient } from "mongodb";
import isEqual from "react-fast-compare";

const uri = `mongodb://username:password@www.doffy.xyz:27017/?authSource=admin&readPreference=primary&serverSelectionTimeoutMS=5000&directConnection=true&ssl=false`;

const client = new MongoClient(uri);
client.connect();
const mongoDb = client.db("doffy");

const query = async () => {
    const listOldConversation = await (
        await mongoDb
            .collection("__old_chat_conversation")
            .find({}, { session: client.startSession() })
    ).toArray();

    const checkListConversations: Array<any> = [];

    listOldConversation.forEach(async (conversation) => {
        if (conversation.type !== 2) {
            const checkHadBefore = checkListConversations.find((item) =>
                isEqual(item.list_users, conversation.list_user.sort())
            );

            if (checkHadBefore) {
                checkListConversations.every(async (item) => {
                    if (
                        isEqual(item.list_users, conversation.list_user.sort())
                    ) {
                        item.total_messages += conversation.total_messages;
                        await mongoDb.collection("chat_message").updateMany(
                            {
                                conversation_id: String(conversation._id),
                            },
                            {
                                $set: {
                                    conversation_id: String(item._id),
                                },
                            }
                        );
                        return false;
                    }
                    return true;
                });
            } else {
                const userData: any = {};
                const listUniqueUser: Array<number> = [];
                conversation.list_user.forEach((user_id: number) => {
                    if (!listUniqueUser.includes(user_id)) {
                        listUniqueUser.push(user_id);
                    }
                });
                listUniqueUser.sort();
                listUniqueUser.forEach((user_id) => {
                    userData[String(user_id)] = {
                        created: "start",
                        modified: conversation.created,
                    };
                });

                const newConversation = {
                    _id: conversation._id,
                    list_users: conversation.list_user.sort(),
                    conversation_name: "",
                    conversation_image: conversation?.image,
                    color: conversation.color,
                    created:
                        conversation?.created ||
                        conversation?.modified ||
                        new Date(),
                    modified: conversation?.modified || new Date(),
                    user_data: userData,
                    total_messages: conversation.total_messages,
                    latest_message: "",
                    status: {
                        value: 1,
                    },
                };

                checkListConversations.push(newConversation);
                await mongoDb
                    .collection("chat_conversation")
                    .insertOne(newConversation);
            }
        }
    });
};

query();
