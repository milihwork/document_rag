import { app } from './app';
import { config } from './config';

app.listen(config.port, '0.0.0.0', () => {
  console.info(`Document RAG Gateway listening on http://0.0.0.0:${config.port}`);
});
