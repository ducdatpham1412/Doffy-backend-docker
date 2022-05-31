import { CronJob } from "cron";
import { Client, Intents, MessageEmbed } from "discord.js";

const morningMessage = new MessageEmbed()
    .setTitle(`Good morning <@everyone>`)
    .setDescription("Chúc cả nhà một ngày làm việc hiệu quả 💥")
    .setColor("GOLD")
    .setImage(
        "https://media4.giphy.com/media/l2olcETxXQjImhNcm2/giphy.gif?cid=ecf05e47fraom88li8hdp0ljov9eufi8n5q8tmbf3wzzp4n5&rid=giphy.gif&ct=g"
    );

const morningMessageLastWeek = new MessageEmbed()
    .setTitle(`Good morning <@everyone>`)
    .setDescription("Chúc cả nhà ngày cuối tuần vui vẻ 💥")
    .setColor("GOLD")
    .setImage(
        "https://media4.giphy.com/media/l2olcETxXQjImhNcm2/giphy.gif?cid=ecf05e47fraom88li8hdp0ljov9eufi8n5q8tmbf3wzzp4n5&rid=giphy.gif&ct=g"
    );

const goodNightMessage = new MessageEmbed()
    .setTitle(`Good night <@everyone>`)
    .setDescription("Đi ngủ thuii, thức khuya sẽ ảnh hưởng đến sức khoẻ 😴")
    .setColor("GOLD")
    .setImage(
        "https://media1.giphy.com/media/jZC7j19LG8s6zsLnoL/giphy.gif?cid=ecf05e470c34sgfzjawmvpwwmzjohxt5ckoef7ml5bmpp6yn&rid=giphy.gif&ct=g"
    );

const remindWeeklyMeeting = new MessageEmbed()
    .setTitle(`BÁO CÁO WEEKLY MEETING <@everyone>`)
    .setDescription(
        "Tối nay ta sẽ có buổi họp, mọi người chú ý điền báo cáo:\nhttps://docs.google.com/spreadsheets/d/1iQVhVffoHQRixVxU13q8eWC3lIH_H5n0kzyprKLQXFA/edit?usp=sharing"
    )
    .setColor("GOLD")
    .setImage(
        "https://media2.giphy.com/media/kHZu4LDtvpY63RT1He/giphy.gif?cid=ecf05e47og5bunp51tjuw9yr4azasgodt3zzzjjit0anx4mv&rid=giphy.gif&ct=g"
    );

// const test = new MessageEmbed()
//     .setTitle(`Start working <@everyone>`)
//     .setDescription("Okay ")
//     .setColor("GOLD")
//     .setImage(
//         "https://media4.giphy.com/media/RhQ7bHvqAbySEm5euO/giphy.gif?cid=ecf05e47uvhvyo4vvyk7hy5zldxywwtpfex1mi5yp4t7uccd&rid=giphy.gif&ct=g"
//     );

export const startBotDiscord = () => {
    if (process.env.ENVIRONMENT_TYPE === "production") {
        const client = new Client({
            intents: [Intents.FLAGS.GUILDS, Intents.FLAGS.GUILD_MESSAGES],
        });

        client.on("ready", () => {
            console.log("Doffy assistant had been ready");
            client.channels.fetch("956027516047482933").then((channels) => {
                // channels.send({ embeds: [test] });

                // good morning message
                new CronJob("00 30 08 * * 1-5", () => {
                    channels.send({ embeds: [morningMessage] });
                }).start();
                new CronJob("00 30 08 * * 0,6", () => {
                    channels.send({ embeds: [morningMessageLastWeek] });
                }).start();

                // good night message
                new CronJob("00 50 23 * * *", () => {
                    channels.send({ embeds: [goodNightMessage] });
                }).start();

                // weekly meeting
                new CronJob("00 30 20 * * 1,4", () => {
                    channels.send({ embeds: [remindWeeklyMeeting] });
                }).start();
            });
        });

        client.login(
            "OTgwNzkwOTMyNjM3MDg5Nzky.GqOM3E.zs8nXc4CXu3aKAF5lvE_vF9PCYd7oq9Z60fTZg"
        );
    } else {
        console.log("This is development env, should not run discord bot");
    }
};

// const test = new MessageEmbed()
//     .setTitle(`Test <@everyone>`)
//     .setDescription("2324232222")
//     .setColor("GOLD");

// client.on("messageCreate", async (message) => {
//     console.log("interaction: ", message.content);
//     if (message.content === "ping") {
//         message.channel.send({ embeds: [SlapEmbed] });
//     }
// });
