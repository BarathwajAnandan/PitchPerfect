const express = require('express');
const app = express();
const port = 3000; // or whatever port you're using

// Serve static files from the current directory
app.use(express.static('.'));

let clients = [];

app.use((req, res, next) =>
{
    res.header('Access-Control-Allow-Origin', 'http://localhost:8000');
    res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
    next();
});

app.get('/events', (req, res) =>
{
    res.writeHead(200, {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive'
    });
    
    clients.push(res);
    
    req.on('close', () =>
    {
        clients = clients.filter(client => client !== res);
    });
});

app.get('/control/:command/:slideNumber?', (req, res) =>
{
    console.log('Received control request:', req.params);
    let command = req.params.command;
    const slideNumber = parseInt(req.params.slideNumber, 10);
    
    if (command.startsWith('slide') && (slideNumber < 1 || slideNumber > 10))
    {
        return res.status(400).send('Slide number must be between 1 and 10');
    }
    
    console.log(`Received command: ${command} for slide number: ${slideNumber}`);


    if (command === 'next' || command === 'prev' || command.startsWith('slide'))
    {
      if (command.startsWith('slide'))
      {
        command = `slide/${slideNumber}`;
      }

        console.log('Sending command to clients:', command);
        clients.forEach(client => client.write(`data: ${command}\n\n`));
        res.send(`Sent ${command} command`);
    }
    else
    {
        res.status(400).send('Invalid command');
    }
});

app.listen(port, () =>
{
    console.log(`Server running at http://localhost:${port}`);
});
