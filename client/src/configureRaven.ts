import * as Raven from 'raven-js';
import { b64DecodeUnicode } from './constants/utils';

const configureRaven = () => {
  if (process.env.NODE_ENV === 'production') {
    const dsn = 'aHR0cHM6Ly85NTZmODkwNDdhYTk0ZGQ1ODU4Mjg0N2E5YjVjMzliZEBzZW50cnkuaW8vMTE5NzU5OA==';
    Raven.config(b64DecodeUnicode(dsn)).install();
  }
};

export default configureRaven;
